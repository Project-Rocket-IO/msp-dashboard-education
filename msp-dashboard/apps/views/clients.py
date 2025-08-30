from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.urls import reverse
from rbac.decorators import has_permission
from apps.models import (
    ClientCompanyFiles,
    ClientLocations,
    ClientWorkTypeRate,
    ClientCompany,
    QuickBooksCustomer,
    QuickBooksInvoice
)
from apps.forms import *
from django.contrib import messages
from rbac.decorators import has_permission
import json 

################
# Client Company


@has_permission("apps.view_clientcompany")
def apps_client_companies_view(request, pk):
    technicians = TechnicianUser.objects.all()
    companies = ClientCompany.objects.all().order_by("-id")
    if companies:
        company = ClientCompany.objects.get(pk=pk)
    return render(
        request,
        "apps/client/apps-client-companies.html",
        {"companies": companies, "company": company, "technicians": technicians},
    )


def create_location(client):
    if client.address_1 and client.city and client.state and client.zip:
        ClientLocations.objects.create(
            name=f"{client.name} @ ",
            client=client,
            address_1=client.address_1,
            city=client.city,
            state=client.state,
            zip=client.zip,
            phone=client.phone,
            email=client.email,
        )


@has_permission("apps.view_clientcompany")
def apps_client_companies_list_view(request):
    companies = ClientCompany.objects.all().order_by("-id")
    technicians = TechnicianUser.objects.all()
    # TODO: Filter the Quickbooks Customers, such that only non-utilized Quickbooks Customers are shown (Implement Unique Constraints on Quickbooks Customer Model)
    # TODO: Quickbooks Customers needs to come from Quickbooks API
    # Get only QuickBooks customers that are not already linked to a client
    qb_customers = QuickBooksCustomer.objects.filter(msp_client__isnull=True)
    qb_invoices = QuickBooksInvoice.objects.filter(customer__msp_client__isnull=True)


    qb_invoices_json = []

    for invoice in qb_invoices:
        qb_invoices_json.append({
            "id": invoice.id,
            "customer": invoice.customer.id,
            "docNumber": invoice.docNumber,
            "amount": float(invoice.amount)
        })

    if request.method == "POST":
        if not request.user.has_perm("apps.add_clientcompany"):
            raise PermissionDenied

        form = ClientCompanyAddForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            # Construct name from first and last name
            contact_first = form.cleaned_data.get('contact_first', '')
            contact_last = form.cleaned_data.get('contact_last', '')
            full_name = f"{contact_first} {contact_last}".strip()
            
            # Set the name field before saving
            instance = form.save(commit=False)
            instance.name = full_name
            instance.save()
            
            messages.success(request, "Company inserted successfully!")
            return redirect("apps:client.companies")
        else:
            form_errors = form.errors.as_text()
            print(form_errors)
            messages.error(request, f"Something went wrong")
            return redirect("apps:client.companies")
    return render(
        request,
        "apps/client/apps-client-companies.html",
        {
            "companies": companies,
            "technicians": technicians,
            "qb_customers": qb_customers,
            "qb_invoices": qb_invoices_json,
        },
    )


# Function to check if the phone number only contains the country code
def is_only_country_code(phone):
    # Convert to a PhoneNumber object
    phone_number_obj = to_python(phone)
    return phone_number_obj and not phone_number_obj.national_number


@has_permission("apps.change_clientcompany")
def apps_update_client_companies_view(request, pk):
    """This function is responsible for Updating the Client Company through the
    Edit Tab in the endpoint: /apps/client/details/<pk>"""

    company = ClientCompany.objects.get(pk=pk)
    if request.method == "POST":
        ## ? Explicit is better than implicit, even though the browser/client-side will never send the QuickBooks Customer ID in the request.
        # TODO: We might need to delete this though, as it's not needed.
        # Check if QuickBooks customer is being changed
        if company.quickbooks_customer and request.POST.get(
            "quickbooks_customer"
        ) != str(company.quickbooks_customer.id):
            messages.warning(
                request,
                "QuickBooks customer cannot be changed once linked. Please contact support if you need to change this.",
            )
            return redirect("apps:client.companies")

        # Make a mutable copy of request.POST
        post_data = request.POST.copy()

        fax = post_data.get("fax")
        phone = post_data.get("phone")
        if is_only_country_code(phone):
            post_data.pop("phone", None)
        if is_only_country_code(fax):
            post_data.pop("fax", None)

        form = ClientCompanyUpdateForm(
            request.POST or None, request.FILES or None, instance=company
        )

        if form.is_valid():
            # Construct name from first and last name
            contact_first = form.cleaned_data.get('contact_first', '')
            contact_last = form.cleaned_data.get('contact_last', '')
            full_name = f"{contact_first} {contact_last}".strip()
            
            # Set the name field before saving
            instance = form.save(commit=False)
            instance.name = full_name
            instance.save()
            
            messages.success(request, "Client Updated successfully!")
            files = request.FILES.getlist("files")
            for file in files:
                if file:
                    # Truncate the file name to 100 characters if necessary
                    file.name = file.name[:100]
                    clientCompanyFile = ClientCompanyFiles(file=file, client=instance)
                    clientCompanyFile.save()
                    print("Saved File ID:", clientCompanyFile.id)

        else:
            form_errors = form.errors.as_text()
            messages.error(request, f"Something went wrong")

    # Check if the request came from the profile page
    referer = request.META.get('HTTP_REFERER', '')
    if 'pages/profile' in referer:
        # Extract the profile ID from the referer URL
        import re
        profile_match = re.search(r'/pages/profile/(\d+)', referer)
        if profile_match:
            profile_id = profile_match.group(1)
            return redirect(f"/pages/pages/profile/{profile_id}")
    
    # Default redirect to client companies list
    return redirect("apps:client.companies")


@has_permission("apps.delete_clientcompany")
def apps_delete_client_companies_view(request, pk):
    companies = ClientCompany.objects.get(pk=pk)
    companies.delete()
    messages.success(request, "Contact deleted successfully!")
    return redirect("apps:client.companies")


@has_permission("apps.add_clientlocations")
def apps_client_locations_view(request, pk):
    company = ClientCompany.objects.get(pk=pk)
    if request.method == "POST":
        form = ClientLocationsAddForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Company Location inserted successfully!")
            return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))
        else:
            print(form.errors)
            messages.error(request, "Something went wrong!")
            return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))
    return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))


@has_permission("apps.change_clientlocations")
def apps_client_locations_update(request, pk, id):
    company = ClientCompany.objects.get(pk=pk)
    location = ClientLocations.objects.get(id=id)

    if request.method == "POST":
        form = ClientLocationsAddForm(request.POST, request.FILES, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, "Company Location inserted successfully!")
            return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))
        else:
            messages.error(request, "Something went wrong!")
            return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))
    return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))


@has_permission("apps.delete_clientlocations")
def apps_client_locations_delete(request, pk, id):
    company = ClientCompany.objects.get(pk=pk)
    location = ClientLocations.objects.get(id=id)
    location.delete()
    messages.success(request, "Location deleted successfully!")
    return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))


@has_permission("apps.change_clientteammembers")
def apps_client_teammembers_update(request, pk, id):
    company = ClientCompany.objects.get(pk=pk)
    clientTeamMember = ClientTeamMembers.objects.get(id=id)
    if request.method == "POST":
        form = ClientTeamMembersAddForm(
            request.POST or None, request.FILES or None, instance=clientTeamMember
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Client Team Members updated successfully!")
            return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))
        else:
            print(form.errors)
            messages.error(request, "Something went wrong!")
            return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))
    return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))


@has_permission("apps.add_clientteammembers")
def create_clientteammember(request, company):
    print(request.POST)
    form = ClientTeamMembersAddForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Client Team Members inserted successfully!")
    else:
        print(request.POST.get("work_phone"))
        print(form.errors)
        messages.error(request, "Something went wrong!")
    return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))


@has_permission("apps.view_clientteammembers")
def apps_client_teammembers_view(request, pk):
    company = get_object_or_404(ClientCompany, pk=pk)
    location = ClientLocations.objects.filter(client_id=pk)
    context = {"company": company, "location": location}

    if request.method == "POST":
        return create_clientteammember(request, company)

    return redirect(
        reverse("apps:client.details", kwargs={"pk": company.pk}), context=context
    )


@has_permission("delete_clientteammembers")
def apps_client_member_delete(request, pk, id):
    company = ClientCompany.objects.get(pk=pk)
    teammate = ClientTeamMembers.objects.get(id=id)
    teammate.delete()
    messages.success(request, "Location deleted successfully!")
    return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))


# @has_permission("apps.view_clientcompany")
# def apps_client_details_companies_view(request, pk):
#     company = ClientCompany.objects.get(pk=pk)
#     projects = ProjectList.objects.filter(client_id=company)
#     tickets = TicketList.objects.filter(client_id=company)
#     client_files = ClientCompanyFiles.objects.filter(client_id=pk)
#     client_locations = ClientLocations.objects.filter(client_id=pk)
#     client_members = ClientTeamMembers.objects.filter(client_id=pk)

#     clients = ClientCompany.objects.all().order_by("-name")
#     technicians = TechnicianUser.objects.all()
#     all_tickets = TicketList.objects.all()
#     all_projects = ProjectList.objects.all()

#     context = {
#         "technicians": technicians,
#         "tickets": tickets,
#         "all_tickets": all_tickets,
#         "clients": clients,
#         "projects": projects,
#         "all_projects": all_projects,
#         "company": company,
#         "client_files": client_files,
#         "client_locations": client_locations,
#         "client_members": client_members,
#     }

#     if request.method == "POST":
#         if "ticketsubmission" in request.POST:
#             form = TicketListAddForm(request.POST or None, request.FILES or None)
#             message = messages.success(request, "Ticket Created!")
#         elif "projectsubmission" in request.POST:
#             form = ProjectListAddForm(request.POST or None, request.FILES or None)
#             message = messages.success(request, "Project Created!")

#         if form.is_valid():
#             context["form"] = form
#             form.save()
#             message
#             return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))
#         else:
#             print(form.errors)
#             messages.error(request, "Something went wrong!")
#             return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))

#     return render(request, "apps/client/apps-client-details.html", context=context)


def get_company_and_location(pk):
    company = get_object_or_404(ClientCompany, pk=pk)
    location = ClientLocations.objects.filter(client_id=pk)
    return company, location


def handle_form_submission(request, company):
    form = ClientTeamMembersAddForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Client Team Members inserted successfully!")
    else:
        print(request.POST.get("work_phone"))
        print(form.errors)
        messages.error(request, "Something went wrong!")
    return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))


@has_permission("apps.view_clientteammembers", "apps.add_clientteammembers")
def apps_client_teammembers_view(request, pk):
    company, location = get_company_and_location(pk)
    context = {"company": company, "location": location}

    if request.method == "POST":
        return handle_form_submission(request, company)

    return redirect(
        reverse("apps:client.details", kwargs={"pk": company.pk}), context=context
    )


@has_permission("apps.add_ticketlist")
def create_client_ticket(request, company):
    form = TicketListAddForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Ticket Created!")
    else:
        print(form.errors)
        messages.error(request, "Something went wrong while creating the ticket!")
    return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))


@has_permission("apps.add_projectlist")
def create_client_project(request, company):
    form = ProjectListAddForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Project Created!")
    else:
        print(form.errors)
        messages.error(request, "Something went wrong while creating the project!")
    return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))


def handle_client_detail_page_post_request(request, company):
    if "ticketsubmission" in request.POST:
        return create_client_ticket(request, company)
    elif "projectsubmission" in request.POST:
        return create_client_project(request, company)
    else:
        return None


@has_permission(
    "apps.view_clientcompany",
    "apps.add_ticketlist",
    "apps.add_projectlist",
    condition="OR",
)
def apps_client_details_companies_view(request, pk):
    company = get_object_or_404(ClientCompany, pk=pk)

    # Handle POST request asap on top, to avoid unnecessary database queries
    if request.method == "POST":
        result = handle_client_detail_page_post_request(request, company)
        if result:
            return result

    projects = ProjectList.objects.filter(client_id=company)
    tickets = TicketList.objects.filter(client_id=company)
    client_files = ClientCompanyFiles.objects.filter(client_id=pk)
    client_locations = ClientLocations.objects.filter(client_id=pk)
    client_members = ClientTeamMembers.objects.filter(client_id=pk)
    clients = ClientCompany.objects.all().order_by("-name")
    technicians = TechnicianUser.objects.all()
    all_tickets = TicketList.objects.all()
    all_projects = ProjectList.objects.all()

    from django.core.paginator import Paginator
    from rbac.utils import paginate_queryset

    client_tickets_page_number = request.GET.get("client_ticket_page", 1)
    tickets, ticketsPaginator = paginate_queryset(
        tickets, client_tickets_page_number, per_page=8
    )

    query_params_pagination_type = request.GET.get(
        "client_ticket_page"
    ) or request.GET.get("client_project_page")

    active_tab = "overview"
    if query_params_pagination_type:
        if "client_ticket_page" in request.GET:
            active_tab = "tickets"
        elif "client_project_page" in request.GET:
            active_tab = "projects"

    context = {
        "technicians": technicians,
        "tickets": tickets,
        "ticketPaginator": ticketsPaginator,
        "all_tickets": all_tickets,
        "clients": clients,
        "projects": projects,
        "all_projects": all_projects,
        "company": company,
        "client_files": client_files,
        "client_locations": client_locations,
        "client_members": client_members,
        "active_tab": active_tab,
    }

    return render(request, "apps/client/apps-client-details.html", context=context)


def apps_client_threshold_view(request, pk):
    company = get_object_or_404(ClientCompany, pk=pk)
    if request.method == "POST":
        company.threshold = request.POST.get("threshold")
        company.save()
        messages.success(request, "Threshold updated successfully!")
    else:
        messages.error(request, "Something went wrong while updating the threshold!")

    return redirect(reverse("apps:client.details", kwargs={"pk": company.pk}))



