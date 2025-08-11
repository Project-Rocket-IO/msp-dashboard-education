from apps.models import QuickBooksToken
from intuitlib.client import AuthClient
from intuitlib.exceptions import AuthClientError
from quickbooks import QuickBooks
from quickbooks.objects.invoice import Invoice
from quickbooks.objects.salesreceipt import SalesReceipt
from quickbooks.objects.payment import Payment
from quickbooks.objects.customer import Customer
from django.conf import settings


def get_auth_client():
    # Let's make it available to the whole app (the server) for each session
    # Each user will have their own auth client, staying the same for the duration of the session
    auth_client = AuthClient(
        settings.QUICKBOOKS_CLIENT_ID,
        settings.QUICKBOOKS_CLIENT_SECRET,
        settings.QUICKBOOKS_REDIRECT_CALLBACK_URL,
        settings.QUICKBOOKS_ENVIRONMENT,
    )

    return auth_client


def get_qb(realm_id, auth_client):
    # Let's make it available to the whole app (the server) for each session
    # Each user will have their own auth client, staying the same for the duration of the session
    try:
        tokenObject = QuickBooksToken.objects.get(realm_id=realm_id)
        refresh_token = tokenObject.refresh_token
        realm_id = tokenObject.realm_id
    except QuickBooksToken.DoesNotExist:
        return None

    try:
        qb = QuickBooks(
            auth_client=auth_client,
            refresh_token=refresh_token,
            company_id=realm_id,
        )
    except AuthClientError as e:
        # refresh token expired
        print("Refresh token expired")
        return None
    return qb


def get_invoice_by_id(realm_id, invoice_id):
    auth_client = get_auth_client()
    qb = get_qb(realm_id, auth_client)
    invoice = Invoice.filter(qb=qb, max_results=1, Id=invoice_id)[0]
    return invoice


def get_all_invoices(realm_id):
    # Use "CustomerRef = '{customer_id}'" to filter by customer
    # Use "DocNumber = '{doc_number}'" to filter by invoice number
    auth_client = get_auth_client()
    if auth_client is None:
        return None
    qb = get_qb(realm_id, auth_client)
    if qb is None:
        return None
    invoices = Invoice.all(qb=qb)
    return invoices


def get_invoice_by_customer(realm_id, customer_id):
    auth_client = get_auth_client()
    qb = get_qb(realm_id, auth_client)
    invoices = Invoice.filter(qb=qb, max_results=20, CustomerRef=customer_id)
    # invoice.CustomerRef, invoice.DocNumber, invoice.TotalAmt, invoice.Balance
    # invoice.TxnDate, invoice.DueDate
    return invoices


def get_all_sales_receipts(realm_id):
    auth_client = get_auth_client()
    qb = get_qb(realm_id, auth_client)
    sales = SalesReceipt.all(qb=qb)
    return sales


def get_sales_receipt_by_customer(realm_id, customer_id):
    auth_client = get_auth_client()
    qb = get_qb(realm_id, auth_client)
    sales = SalesReceipt.filter(qb=qb, max_results=20, CustomerRef=customer_id)
    # sale.CustomerRef, sale.DocNumber, sale.TotalAmt, sale.Balance
    # sale.TxnDate, sale.DueDate
    return sales


def get_payment_by_id(realm_id, payment_id):
    auth_client = get_auth_client()
    qb = get_qb(realm_id, auth_client)
    payment = Payment.filter(qb=qb, max_results=1, Id=payment_id)[0]
    return payment


def get_all_customers(realm_id, auth_client=None, qb=None):
    if auth_client is None:
        auth_client = get_auth_client()
    if qb is None:
        qb = get_qb(realm_id, auth_client)
    customers = Customer.all(qb=qb)
    return customers


def get_customer_by_id(realm_id, customer_id, auth_client=None, qb=None):
    if auth_client is None:
        auth_client = get_auth_client()
    if qb is None:
        qb = get_qb(realm_id, auth_client)
    customer = Customer.filter(qb=qb, max_results=1, Id=customer_id)[0]
    return customer
