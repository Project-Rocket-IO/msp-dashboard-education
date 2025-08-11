from auditlog.models import LogEntry
from django.shortcuts import redirect, render
from apps.models import (
    LeadCompany,
    LeadFiles,
    LeadOpportunity,
)
from apps.forms import *
from django.contrib import messages
from rbac.decorators import has_permission
from rbac.subscription_access import require_subscription_feature


# Leads Contact views
@has_permission("apps.view_leadcompany")
@require_subscription_feature("leads")
def apps_leads_view(request):
    leads = LeadCompany.objects.all().order_by("-id")
    if request.method == "POST":
        form = LeadCompanyAddForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            instance = form.save()
            messages.success(request, "Lead inserted successfully!")
            return redirect("apps:leads")
        else:
            print(request.POST.get("phone"))
            print(request.POST.get("fax"))
            print(form.errors)
            messages.error(request, "Something went wrong!")
            return redirect("apps:leads")
    return render(request, "apps/leads/apps-leads.html", {"leads": leads})


@require_subscription_feature("leads")
def apps_leads_detail_view(request, pk):
    leads = LeadCompany.objects.get(pk=pk)
    leads_log = LogEntry.objects.get_for_object(leads)
    leads_files = LeadFiles.objects.filter(lead_id=pk)
    leads_files_log = LogEntry.objects.get_for_objects(leads_files)
    try:
        leads_opportunity = LeadOpportunity.objects.filter(lead_id=pk).latest("id")
        opportunity_log = LogEntry.objects.get_for_objects(
            LeadOpportunity.objects.filter(lead_id=pk)
        )
    except:
        leads_opportunity = None
        opportunity_log = None

    technicians = TechnicianUser.objects.all()
    context = {
        "leads": leads,
        "leads_files": leads_files,
        "technicians": technicians,
        "leads_opportunity": leads_opportunity,
        "leads_log": leads_log,
        "opportunity_log": opportunity_log,
        "leads_files_log": leads_files_log,
    }

    if request.method == "POST":
        form = LeadOpportunityAddForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Opportunity inserted successfully!")
            return redirect(request.META.get("HTTP_REFERER"))
        else:
            print(form.errors)
            messages.error(request, "Something went wrong!")
            return redirect(request.META.get("HTTP_REFERER"))
    return render(request, "apps/leads/apps-leads-detail.html", context=context)


@require_subscription_feature("leads")
def apps_leads_add_view(request):
    leads = LeadCompany.objects.all().order_by("-id")

    if request.method == "POST":
        form = LeadCompanyAddForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Contact inserted successfully!")
            return redirect("apps:crm.contacts")
        else:
            messages.error(request, "Something went wrong!")
            return redirect("apps:crm.contacts")
    return render(request, "apps/leads/apps-crm-contacts.html", {"leads": leads})


@has_permission("apps.change_leadcompany")
@require_subscription_feature("leads")
def apps_leads_update_view(request, pk):
    lead = LeadCompany.objects.get(pk=pk)
    context = {"lead": lead}
    if request.method == "POST":
        form = LeadCompanyUpdateForm(
            request.POST or None, request.FILES or None, instance=lead
        )
        if form.is_valid():
            lead = form.save()
            lead.save()

            files = request.FILES.getlist("files")
            for file in files:
                if file:
                    # Truncate the file name to 100 characters if necessary
                    file.name = file.name[:100]
                    leadFile = LeadFiles(file=file, lead=lead)
                    leadFile.save()
                    print("Saved File ID:", leadFile.id)

            messages.success(request, "Lead Updated successfully!")
            return redirect(request.META.get("HTTP_REFERER"))

        else:
            print(form.errors)
            print(f"Files: {request.FILES}")
            messages.error(request, "Something went wrong!")
            return redirect(request.META.get("HTTP_REFERER"))

    return render(request, "apps/leads/apps-leads-update.html", context=context)


@has_permission("apps.delete_leadcompany")
def apps_leads_delete_view(request, pk):
    leads = LeadCompany.objects.get(pk=pk)
    leads.delete()
    messages.success(request, "Contact deleted successfully!")
    return redirect("apps:leads")
