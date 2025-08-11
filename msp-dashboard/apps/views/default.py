from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class AppsView(LoginRequiredMixin, TemplateView):
    pass


# Calendar
apps_calendar_view = AppsView.as_view(template_name="apps/apps-calendar.html")

# Support Tickets
apps_tickets_list_view = AppsView.as_view(
    template_name="apps/support-tickets/apps-tickets-list.html"
)
apps_tickets_delete_list_view = AppsView.as_view(
    template_name="apps/support-tickets/apps-tickets-list.html"
)
apps_tickets_details_view = AppsView.as_view(
    template_name="apps/support-tickets/apps-tickets-details.html"
)
apps_ticket_download_file = AppsView.as_view(
    template_name="apps/support-tickets/apps-tickets-details.html"
)
apps_technician_labor_view = AppsView.as_view(
    template_name="apps/support-tickets/apps-tickets-details.html"
)
apps_tickets_comments_view = AppsView.as_view(
    template_name="apps/support-tickets/apps-tickets-details.html"
)
apps_tickets_replies_view = AppsView.as_view(
    template_name="apps/support-tickets/apps-tickets-details.html"
)
apps_tickets_edit_view = AppsView.as_view(
    template_name="apps/support-tickets/apps-tickets-update.html"
)

# Projects
apps_projects_list_view = AppsView.as_view(
    template_name="apps/projects/apps-projects-list.html"
)
apps_projects_edit_list_view = AppsView.as_view(
    template_name="apps/projects/apps-projects-update.html"
)
apps_projects_overview_view = AppsView.as_view(
    template_name="apps/projects/apps-projects-overview.html"
)
apps_projects_remove_ticket_view = AppsView.as_view(
    template_name="apps/projects/apps-projects-overview.html"
)
apps_projects_remove_tech_view = AppsView.as_view(
    template_name="apps/projects/apps-projects-overview.html"
)
apps_projects_comments_view = AppsView.as_view(
    template_name="apps/projects/apps-projects-overview.html"
)
apps_projects_replies_view = AppsView.as_view(
    template_name="apps/projects/apps-projects-overview.html"
)
apps_projects_create_view = AppsView.as_view(
    template_name="apps/projects/apps-projects-create.html"
)
apps_projects_delete_list_view = AppsView.as_view(
    template_name="apps/projects/apps-projects-list.html"
)
apps_projects_download_file = AppsView.as_view(
    template_name="apps/support-tickets/apps-tickets-details.html"
)

# Client Companies
apps_client_companies_view = AppsView.as_view(
    template_name="apps/client/apps-client-companies.html"
)
apps_add_client_companies_view = AppsView.as_view(
    template_name="apps/client/apps-client-companies.html"
)
apps_update_client_companies_view = AppsView.as_view(
    template_name="apps/client/apps-client-companies.html"
)
apps_client_details_companies_view = AppsView.as_view(
    template_name="apps/client/apps-client-details.html"
)
apps_delete_client_companies_view = AppsView.as_view(
    template_name="apps/client/apps-client-companies.html"
)
# apps_crm_leads_view = AppsView.as_view(template_name="apps/crm/apps-crm-leads.html")

# Leads
apps_leads_view = AppsView.as_view(template_name="apps/leads/apps-leads.html")
apps_leads_detail_view = AppsView.as_view(
    template_name="apps/leads/apps-leads-detail.html"
)

# Sales
apps_sales_deals_view = AppsView.as_view(
    template_name="apps/sales/apps-sales-deals.html"
)

# Filemanager
apps_filemanager = AppsView.as_view(template_name="apps/filemanager/overview.html")
apps_filemanager_delete_file = AppsView.as_view(template_name="apps/filemanager.html")
apps_filemanager_download_file = AppsView.as_view(template_name="apps/filemanager.html")
apps_filemanager_upload_file = AppsView.as_view(template_name="apps/filemanager.html")
apps_filemanager_create_usrdir = AppsView.as_view(
    template_name="apps/filemanager/overview.html"
)

# Webview
webview_urls_view = AppsView.as_view(template_name="apps/webview/apps-webview.html")
webview_update_view = AppsView.as_view(template_name="apps/webview/apps-webview.html")
webview_delete_view = AppsView.as_view(template_name="apps/webview/apps-webview.html")

# Mail Box
apps_mailbox_view = AppsView.as_view(template_name="apps/email/apps-mailbox.html")
apps_basicaction_view = AppsView.as_view(
    template_name="apps/email/apps-email-basic.html"
)
apps_invoiceaction_view = AppsView.as_view(
    template_name="apps/email/apps-email-ecommerce.html"
)


apps_todo_view = AppsView.as_view(template_name="apps/apps-todo.html")
apps_api_key_view = AppsView.as_view(template_name="apps/apps-api-key.html")
