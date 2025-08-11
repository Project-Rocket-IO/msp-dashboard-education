from quickbooks.exceptions import QuickbooksException
from apps.models import QuickBooksCustomer, ClientCompany, QuickBooksInvoice
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from intuitlib.exceptions import AuthClientError
from django.shortcuts import render, redirect
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
)
from django.conf import settings
from apps.models import Invoice, QuickBooksToken, TicketList
import requests
from django.utils import timezone
from django.db.models import Sum
from apps.views.utils import (
    get_invoice_by_customer,
    get_auth_client,
    get_invoice_by_id,
    get_payment_by_id,
    get_all_invoices,
    get_all_customers,
    get_customer_by_id,
)
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal
from rbac.decorators import has_permission

@csrf_exempt
def apps_invoices_create_webhook_view(request):
    """
    This function is used to get updates from the Quickbooks API for the customer, invoice, and payment entities.
    It will be called when a new customer, invoice, or payment is created, updated, or deleted.
    """
    content = request.body.decode("utf-8")

    # Parse the JSON content
    data = json.loads(content)

    # Get the realmId
    realm_id = data["eventNotifications"][0]["realmId"]

    # Get the entities
    entities = data["eventNotifications"][0]["dataChangeEvent"]["entities"]

    #  auth client
    auth_client = get_auth_client()

    
    refresh_token = QuickBooksToken.objects.get(
        realm_id=realm_id
    ).refresh_token
    
    auth_client.refresh(refresh_token=refresh_token)

    # save the new refresh token
    QuickBooksToken.objects.filter(realm_id=realm_id).update(
        refresh_token=auth_client.refresh_token,
        expires_in=auth_client.x_refresh_token_expires_in,
        is_refresh_token_replaced=True
    )

    for entity in entities:
        entity_id = entity["id"]
        entity_name = entity["name"]
        operation = entity["operation"]

        if entity_name == "Invoice":
            try:
                invoice = get_invoice_by_id(realm_id, entity_id)
            except QuickbooksException as e:
                #  if e message = No session manager
                if "No session manager" in str(e):
                    # Refresh token expired
                    QuickBooksToken.objects.filter(realm_id=realm_id).update(
                        is_refresh_token_replaced=False
                    )
                print(e)
                return HttpResponse("Token expired")

            if operation == "Create":  # Very first time the customer is invoiced
                # ? There is a possibility that the customer is not in the database (despite CustomerRef being present)
                # That means the MSP/User created the customer in QB, but not in the dashboard
                # They created Customer and then moved on to create Invoice immediately
                client = ClientCompany.objects.filter(
                    quickbooks_customer__id=invoice.CustomerRef.value
                ).first()
                if not client:
                    return HttpResponse("Customer not found")

                # Create the invoice
                invoice, created = Invoice.objects.get_or_create(
                    id=invoice.Id,
                    client=client,
                    status="Pending",
                )
            elif operation == "Update":  # The customer is invoiced again (Same invoice)
                invoice_obj = Invoice.objects.get(id=invoice.Id)
                invoice_obj.amount = Decimal(invoice.TotalAmt)
                invoice_obj.save()

            elif operation == "Delete":
                invoice = Invoice.objects.get(id=invoice.Id)
                invoice.delete()

        elif entity_name == "Payment":
            try:
                payment = get_payment_by_id(realm_id, entity_id)
            except QuickbooksException as e:
                if "No session manager" in str(e):
                    # Refresh token expired
                    QuickBooksToken.objects.filter(realm_id=realm_id).update(
                        is_refresh_token_replaced=False
                    )
                print(e)
                return HttpResponse("Token expired")

            if operation == "Create":
                client = ClientCompany.objects.filter(
                    quickbooks_customer__id=payment.CustomerRef.value
                ).first()
                if not client:
                    return HttpResponse("Customer not found")

                # Create the payment
                invoice = Invoice.objects.filter(
                    client=client,
                ).first()
                if not invoice:
                    return HttpResponse("Invoice not found")

                # Update the invoice
                invoice.amount_paid += Decimal(payment.TotalAmt)
                invoice.save()

        elif entity_name == "Customer":
            try:
                customer = get_customer_by_id(realm_id, entity_id)
            except QuickbooksException as e:
                if "No session manager" in str(e):
                    # Refresh token expired
                    QuickBooksToken.objects.filter(realm_id=realm_id).update(
                        is_refresh_token_replaced=False
                    )
                print(e)
                return HttpResponse("Webhook received")

            if operation == "Create":  # A new customer was created
                # Add Quickbbooks customer
                QuickBooksCustomer.objects.create(
                    id=customer.Id,
                    name=customer.DisplayName,
                    email=customer.PrimaryEmailAddr,
                )
            elif operation == "Update":  # A customer was updated
                # Update Quickbbooks customer
                qb_customer, created = QuickBooksCustomer.objects.get_or_create(
                    id=customer.Id
                )

                qb_customer.name = customer.DisplayName
                qb_customer.email = customer.PrimaryEmailAddr
                qb_customer.save()
            elif operation == "Delete":  # A customer was deleted
                # TODO: Needs discussion with the team
                QuickBooksCustomer.objects.filter(id=customer.Id).delete()

        else:
            print("--------------------------------")
            print("ENTITY ID #", entity_id)
            print("ENTITY NAME #", entity_name)
            print("--------------------------------")

    return HttpResponse("Webhook received")


def qbo_api_call(access_token, realm_id):
    base_url = settings.QUICKBOOKS_BASE_URL
    route = "/v3/company/{0}/companyinfo/{0}".format(realm_id)
    auth_header = "Bearer {0}".format(access_token)
    headers = {"Authorization": auth_header, "Accept": "application/json"}
    return requests.get("{0}{1}".format(base_url, route), headers=headers)


@has_permission("apps.view_invoice")
def apps_invoices_connect_view(request):
    # If quickbooks is already connected, redirect to the list view
    # update the session check to db check
    # TODO: This isn't ideal. Don't want to call the test function every time
    # TODO: Figure out a better way to check if the refresh token is expired
    # ! Maybe use a background task to keep the refresh token fresh
    try:
        # TODO: Work on this
        msp_company = request.user.mspcompany
        if not msp_company:
            return render(request, "apps/invoices/apps-invoices-connect.html")

        quickbooks_token = msp_company.quickbookstoken
        if not quickbooks_token:
            return render(request, "apps/invoices/apps-invoices-connect.html")

        if (
            quickbooks_token.is_refresh_token_valid
            and quickbooks_token.is_refresh_token_replaced
        ):
            return redirect("apps:invoices.list")
    except (AttributeError, Exception) as e:
        # Log the error if needed
        print(f"Error checking QuickBooks connection: {str(e)}")

    return render(request, "apps/invoices/apps-invoices-connect.html")


def apps_invoices_oauth_view(request):
    auth_client = AuthClient(
        settings.QUICKBOOKS_CLIENT_ID,
        settings.QUICKBOOKS_CLIENT_SECRET,
        settings.QUICKBOOKS_REDIRECT_CALLBACK_URL,
        settings.QUICKBOOKS_ENVIRONMENT,
    )

    url = auth_client.get_authorization_url([Scopes.ACCOUNTING])
    request.session["state"] = auth_client.state_token
    return redirect(url)


def apps_invoices_callback_view(request):
    auth_client = AuthClient(
        settings.QUICKBOOKS_CLIENT_ID,
        settings.QUICKBOOKS_CLIENT_SECRET,
        settings.QUICKBOOKS_REDIRECT_CALLBACK_URL,
        settings.QUICKBOOKS_ENVIRONMENT,
        state_token=request.session.get("state"),
    )

    state_tok = request.GET.get("state", None)
    error = request.GET.get("error", None)

    if error == "access_denied":
        return redirect("apps:invoices.connect")

    if state_tok is None:
        return HttpResponseBadRequest()
    elif state_tok != auth_client.state_token:
        return HttpResponse("unauthorized", status=401)

    auth_code = request.GET.get("code", None)
    realm_id = request.GET.get("realmId", None)
    # ! TODO: Right now, user can change their company and realm_id will change
    request.session["realm_id"] = realm_id

    if auth_code is None:
        return HttpResponseBadRequest()

    try:
        auth_client.get_bearer_token(auth_code, realm_id=realm_id)

        # Store tokens in database
        # Get the token object, if not exists, create it, if exists, update it
        token_object, created = QuickBooksToken.objects.get_or_create(
            mspcompany=request.user.mspcompany,  # ! It's assuming that the user is already connected to an mspcompany
            realm_id=realm_id,
        )
        token_object.refresh_token = auth_client.refresh_token
        token_object.expires_in = auth_client.x_refresh_token_expires_in
        token_object.is_refresh_token_replaced = True
        token_object.save()

        # Create customers from QB to DB
        customers = get_all_customers(realm_id)
        for customer in customers:
            qb_customer, created = QuickBooksCustomer.objects.get_or_create(
                id=customer.Id
            )
            if created:
                qb_customer.name = customer.DisplayName
                qb_customer.email = customer.PrimaryEmailAddr
                qb_customer.save()

        # Create invoices from QB to DB
        invoices = get_all_invoices(realm_id)
        for invoice in invoices:
            try:
                # Validate required fields
                if not hasattr(invoice, "Id") or not invoice.Id:
                    print(f"Skipping invoice - Missing ID")
                    continue

                if not hasattr(invoice, "CustomerRef") or not invoice.CustomerRef.value:
                    print(f"Skipping invoice {invoice.Id} - Missing Customer Reference")
                    continue

                # Get or create the invoice
                qb_invoice, created = QuickBooksInvoice.objects.get_or_create(
                    id=invoice.Id
                )

                # Update customer reference if it exists
                try:
                    customer = QuickBooksCustomer.objects.get(
                        id=invoice.CustomerRef.value
                    )
                    qb_invoice.customer = customer
                    qb_invoice.docNumber = invoice.DocNumber
                    qb_invoice.amount = invoice.TotalAmt
                    qb_invoice.amount_paid = invoice.TotalAmt - invoice.Balance

                except QuickBooksCustomer.DoesNotExist:
                    print(
                        f"Customer {invoice.CustomerRef.value} not found for invoice {invoice.Id}"
                    )
                    continue

                qb_invoice.save()

                if created:
                    print(f"Created new invoice {invoice.Id}")
                else:
                    print(f"Updated existing invoice {invoice.Id}")

            except Exception as e:
                print(
                    f"Error processing invoice {getattr(invoice, 'Id', 'Unknown')}: {str(e)}"
                )
                continue

    except AuthClientError as e:
        print(e.status_code)
        print(e.content)
        print(e.intuit_tid)
    except Exception as e:
        print(e)
    return redirect("apps:invoices.connected")


def apps_invoices_connected_view(request):
    auth_client = get_auth_client()

    return render(
        request,
        "apps/invoices/apps-invoices-connected.html",
        context={"openid": auth_client.id_token is not None},
    )


def apps_invoices_qbo_request_view(request):
    # auth_client = get_auth_client()
    # qb = get_qb(request, auth_client)
    invoices = get_invoice_by_customer(request, "58")

    if invoices is None:
        return HttpResponse("No invoices found")

    return HttpResponse(" ".join([str(invoice.to_json()) for invoice in invoices]))


def apps_invoices_refresh_view(request):
    auth_client = get_auth_client()

    try:
        auth_client.refresh()
    except AuthClientError as e:
        print(e.status_code)
        print(e.intuit_tid)
    return HttpResponse("New refresh_token: {0}".format(auth_client.refresh_token))


def apps_invoices_revoke_view(request):

    auth_client = get_auth_client()
    try:
        is_revoked = auth_client.revoke()
        if is_revoked:
            # remove the tokens from sessions now
            request.session.pop("access_token", None)
            request.session.pop("refresh_token", None)
            request.session.pop("realm_id", None)
            return HttpResponse("Revoke successful")
        else:
            return HttpResponse("Revoke failed")
    except AuthClientError as e:
        print(e.status_code)
        print(e.intuit_tid)
        return HttpResponse("Revoke failed")


@has_permission("apps.view_invoice")
def apps_invoices_list_view(request):
    # Local invoices
    invoices = Invoice.objects.all()

    # Initialize counters
    total_amount_paid = 0
    total_invoices_sent = 0
    unpaid_invoices = 0
    num_invoices_paid = 0
    num_invoices_charged = 0
    total_amount_charged = 0

    # Single loop to calculate all metrics
    for invoice in invoices:
        total_amount_paid += invoice.amount_paid
        total_invoices_sent += invoice.amount
        unpaid_invoices += invoice.amount - invoice.amount_paid
        total_amount_charged += invoice.amount_charged
        if invoice.amount_paid > 0:
            num_invoices_paid += 1
        if invoice.amount_charged > 0:
            num_invoices_charged += 1

    num_invoices_sent = len(invoices)
    num_invoices_unpaid = num_invoices_sent - num_invoices_paid

    return render(
        request,
        "apps/invoices/apps-invoices-list.html",
        {
            "invoices": invoices,
            "total_amount_paid": total_amount_paid / 1000,
            "total_invoices_sent": total_invoices_sent / 1000,
            "unpaid_invoices": unpaid_invoices / 1000,
            "num_invoices_sent": num_invoices_sent,
            "num_invoices_paid": num_invoices_paid,
            "num_invoices_unpaid": num_invoices_unpaid,
            "num_invoices_charged": num_invoices_charged,
            "total_amount_charged": total_amount_charged / 1000,
        },
    )


@has_permission("apps.view_invoice")
def apps_invoices_details_view(request, pk):
    invoice = Invoice.objects.get(pk=pk)
    line_items = TicketList.objects.filter(client=invoice.client, status="Closed")
    # Add hours to line_items
    for line_item in line_items:
        line_item.hours = int(
            line_item.technician_labor.all().aggregate(Sum("minutes"))["minutes__sum"]
            / 60
        )
        line_item.amount = line_item.work_type.rate * line_item.hours
    total_amount = sum([line_item.amount for line_item in line_items])
    return render(
        request,
        "apps/invoices/apps-invoices-details.html",
        {"invoice": invoice, "line_items": line_items, "total_amount": total_amount},
    )


def apps_invoices_create_view(request):
    return render(request, "apps/invoices/apps-invoices-create.html")
