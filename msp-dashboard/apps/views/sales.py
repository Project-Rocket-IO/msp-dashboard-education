from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Sum, Count
from apps.models import SalesRequests
from apps.forms import *
from django.contrib import messages
from rbac.decorators import has_permission
from rbac.subscription_access import require_subscription_feature
from django.core.exceptions import PermissionDenied

#########
# Sales


@has_permission("apps.view_salesrequests")
@require_subscription_feature("sales")
def apps_sales_deals_view(request):
    context = {}
    context.update(get_sales_data(request))
    context.update(get_related_data(request))
    
    # Debug output
    print("DEBUG: Sales view context keys:", list(context.keys()))
    print("DEBUG: new_sale_count:", context.get('new_sale_count'))
    print("DEBUG: new_sale queryset:", list(context.get('new_sale', []).values('name', 'type', 'value', 'client__name')) if context.get('new_sale') else 'No new_sale')

    if request.method == "POST":
        if request.user.has_perm("apps.add_salesrequests"):
            return handle_post_request(request)
        else:
            raise PermissionDenied

    return render(request, "apps/sales/apps-sales-deals.html", context=context)


def get_sales_data(request):
    sales = SalesRequests.objects.all()

    sale_types = [
        "New Sale",
        "Proposal Created",
        "Proposal Sent",
        "Proposal Executed",
        "Sale Closed",
    ]

    sales_data = {}
    for sale_type in sale_types:
        filtered_sales = sales.filter(type=sale_type)
        sales_data[f"{sale_type.lower().replace(' ', '_')}"] = filtered_sales
        sales_data[f"{sale_type.lower().replace(' ', '_')}_count"] = (
            filtered_sales.count()
        )
        sales_data[f"{sale_type.lower().replace(' ', '_')}_sum"] = (
            filtered_sales.aggregate(Sum("value"))["value__sum"] or 0
        )

    sales_data["sales"] = sales
    return sales_data


def get_related_data(request):
    related_data = {}

    if request.user.has_perm("accounts.view_technicianuser"):
        related_data["technicians"] = TechnicianUser.objects.all()

    if request.user.has_perm("apps.view_clientcompany"):
        related_data["clients"] = ClientCompany.objects.all()

    if request.user.has_perm("apps.view_clientteammembers"):
        related_data["contacts"] = ClientTeamMembers.objects.all()

    return related_data


def handle_post_request(request):
    form = SalesRequestsAddForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        form.save()
        messages.success(request, "Sales inserted Successfully!")
        return redirect(request.META.get("HTTP_REFERER"))
    else:
        print(form.errors)
        print(f"Files: {request.FILES}")
        messages.error(request, "Something went wrong!")
        return JsonResponse(
            {"message": "Something went wrong!", "error": str(form.errors)},
            status=400,
        )


@has_permission("apps.delete_salesrequests")
@require_subscription_feature("sales")
def apps_sales_deals_delete_view(request, pk):
    """Sales Delete View
    Pass a primary key, it will get the Sales object and try to delete
    It shows success and error messages depending on outcome.
    Finally, redirect to Sales List page
    """
    sales = get_object_or_404(SalesRequests, pk=pk)

    if request.method == "POST":
        try:
            sales.delete()
            messages.success(request, "Sales deleted successfully!")
        except Exception as e:
            print(e)
            messages.error(request, "Something went wrong!")

    return redirect("apps:sales.deals")


@require_subscription_feature("sales")
def apps_sales_deals_update_view(request, pk):
    sales = SalesRequests.objects.get(pk=pk)
    technicians = TechnicianUser.objects.all()
    clients = ClientCompany.objects.all()
    contacts = ClientTeamMembers.objects.all()
    context = {
        "sales": sales,
        "technicians": technicians,
        "contacts": contacts,
        "clients": clients,
    }
    if request.method == "POST":
        print(f"DEBUG: POST data received: {request.POST}")
        print(f"DEBUG: due_date from POST: '{request.POST.get('due_date')}'")

        form = SalesRequestsAddForm(
            request.POST or None, request.FILES or None, instance=sales
        )

        if form.is_valid():
            # Check if any fields actually changed
            if form.has_changed():
                form.save()
                messages.success(request, "Sales updated Successfully!")
            else:
                messages.info(request, "No changes were made to the sales record.")
            return redirect(request.META.get("HTTP_REFERER"))

        else:
            print(f"DEBUG: Form errors: {form.errors}")
            print(f"DEBUG: Form data: {form.data}")
            print(f"Files: {request.FILES}")
            messages.error(request, "Something went wrong!")
            return JsonResponse(
                {"message": "Something went wrong!", "error": str(form.errors)},
                status=400,
            )

    return render(request, "apps/sales/apps-sales-deals.html", context=context)


def get_contacts(request, client_id):
    print("test")
    contacts = ClientTeamMembers.objects.filter(client_id=client_id).values(
        "pk", "first_name", "last_name"
    )
    print(f"contacts: {contacts}")
    return JsonResponse(list(contacts), safe=False)
