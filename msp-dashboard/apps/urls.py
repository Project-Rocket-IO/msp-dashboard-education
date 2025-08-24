from django.conf.urls import include
from django.urls import path, re_path
from apps.api import api_start_timer, api_discard_timer, api_stop_timer
from apps.views import *
from apps.two_factor_views import TenantAwareTwoFactorSetupView

app_name = "apps"

urlpatterns = [
    # 2FA Setup
    path("two-factor/setup/", TenantAwareTwoFactorSetupView.as_view(), name="two_factor_setup"),
    # API
    path("api/start_timer/<int:pk>", view=api_start_timer, name="api_start_timer"),
    path("api/discard_timer/", view=api_discard_timer, name="api_discard_timer"),
    path("api/stop_timer/<int:pk>", view=api_stop_timer, name="api_stop_timer"),
    # Calendar
    path("calendar/", view=apps_calendar_view, name="calendar"),
    # Stripe
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
    # Projects
    path("projects/list/", view=apps_projects_list_view, name="projects.list"),
    path(
        "projects/overview/<int:pk>",
        view=apps_projects_overview_view,
        name="projects.overview",
    ),
    path(
        "projects/download/<int:pk>",
        view=apps_projects_download_file,
        name="projects.download_file",
    ),
    path(
        "projects/comments/<str:pk>",
        view=apps_projects_comments_view,
        name="projects.comments",
    ),
    path(
        "projects/replies/<int:pk>",
        view=apps_projects_replies_view,
        name="projects.replies",
    ),
    path("projects/create/", view=apps_projects_create_view, name="projects.create"),
    path(
        "projects/delete/<str:pk>",
        view=apps_projects_delete_list_view,
        name="projects.delete_list",
    ),
    path(
        "projects/edit/<str:pk>",
        view=apps_projects_edit_list_view,
        name="projects.edit",
    ),
    path(
        "projects/removeticket/<str:pk>",
        view=apps_projects_remove_ticket_view,
        name="projects.removeticket",
    ),
    path(
        "projects/removetech/<str:project_pk>/<str:tech_pk>",
        view=apps_projects_remove_tech_view,
        name="projects.removetech",
    ),
    path(
        "projects/comments/<int:project_pk>/<int:pk>/toggle-visibility",
        view=apps_projects_comments_toggle_visibility_view,
        name="projects.comments.toggle_visibility",
    ),
    path(
        "projects/replies/<int:project_pk>/<int:pk>/toggle-visibility",
        view=apps_projects_replies_toggle_visibility_view,
        name="projects.replies.toggle_visibility",
    ),
    # Support Tickets
    path("support-tickets/list/", view=apps_tickets_list_view, name="tickets.list"),
    path(
        "support-tickets/create/", view=apps_tickets_create_view, name="tickets.create"
    ),
    path("support-tickets/bulk-upload/", view=apps_tickets_bulk_upload_view, name="tickets.bulk_upload"
    ),
    path(
        "support-tickets/edit/<int:pk>",
        view=apps_tickets_edit_view,
        name="tickets.edit",
    ),
    path(
        "support-tickets/close/<int:pk>",
        view=apps_tickets_close_view,
        name="tickets.close",
    ),
    path(
        "support-tickets/complete/<int:pk>",
        view=apps_tickets_complete_view,
        name="tickets.complete",
    ),
    path(
        "support-tickets/delete/<int:pk>",
        view=apps_tickets_delete_list_view,
        name="tickets.delete_list",
    ),
    path(
        "support-tickets/details/<int:pk>",
        view=apps_tickets_details_view,
        name="tickets.details",
    ),
    path(
        "support-tickets/time/<int:pk>",
        view=apps_technician_labor_view,
        name="tickets.time_entry",
    ),
    path(
        "support-tickets/comments/<int:pk>",
        view=apps_tickets_comments_view,
        name="tickets.comments",
    ),
    path(
        "support-tickets/comments/<int:ticket_pk>/<int:pk>/delete",
        view=apps_tickets_comments_delete_view,
        name="tickets.comments.delete",
    ),
    path(
        "support-tickets/comments/<int:ticket_pk>/<int:pk>/toggle-visibility",
        view=apps_tickets_comments_toggle_visibility_view,
        name="tickets.comments.toggle_visibility",
    ),
    path(
        "support-tickets/replies/<int:pk>",
        view=apps_tickets_replies_view,
        name="tickets.replies",
    ),
    path(
        "support-tickets/replies/<int:ticket_pk>/<int:pk>/toggle-visibility",
        view=apps_tickets_replies_toggle_visibility_view,
        name="tickets.replies.toggle_visibility",
    ),
    path(
        "support-tickets/download/<int:pk>",
        view=apps_ticket_download_file,
        name="tickets.download_file",
    ),
    path(
        "support-tickets/file/<int:pk>/rename",
        view=apps_ticket_file_rename_view,
        name="tickets.file_rename",
    ),
    path(
        "support-tickets/file/<int:pk>/delete",
        view=apps_ticket_file_delete_view,
        name="tickets.file_delete",
    ),
    # Chat
    path("mailbox/", view=apps_mailbox_view, name="mailbox"),
    path("basicaction/", view=apps_basicaction_view, name="basicaction"),
    path("invoiceaction/", view=apps_invoiceaction_view, name="invoiceaction"),
    # Webview Url
    path("webview/links/", view=webview_urls_view, name="webview.links"),
    path("webview/update/<int:pk>", view=webview_update_view, name="webview.update"),
    path("webview/delete/<int:pk>", view=webview_delete_view, name="webview.delete"),
    # Leads Url
    path("leads/", view=apps_leads_view, name="leads"),
    path("leads/details/<int:pk>", view=apps_leads_detail_view, name="leads.detail"),
    path("leads/update/<int:pk>", view=apps_leads_update_view, name="leads.update"),
    path("leads/add_lead/", view=apps_leads_add_view, name="leads.add_leads"),
    path(
        "leads/delete/<int:pk>", view=apps_leads_delete_view, name="leads.delete_leads"
    ),
    # Sales Url
    path("sales/deals/", view=apps_sales_deals_view, name="sales.deals"),
    path(
        "sales/deals/delete/<int:pk>",
        view=apps_sales_deals_delete_view,
        name="sales.deals_delete",
    ),
    path(
        "sales/deals/<int:pk>",
        view=apps_sales_deals_update_view,
        name="sales.deals_update",
    ),
    path("get-contacts/<int:client_id>/", view=get_contacts, name="get_contacts"),
    # Filemanager
    path("filemanager/", view=apps_filemanager, name="filemanager.overview"),
    # path("filemanager/overview/", view=apps_filemanager, name="filemanager.overview"),
    path(
        "filemanager/create_user_directory/<str:pk>",
        view=apps_filemanager_create_usrdir,
        name="filemanager.user_directory",
    ),
    path(
        "filemanager/delete-file/<str:file_path>/",
        view=apps_filemanager_delete_file,
        name="filemanager.delete_file",
    ),
    path(
        "filemanager/upload-file/",
        view=apps_filemanager_upload_file,
        name="filemanager.upload_file",
    ),
    path(
        "filemanager/save-info/<str:file_path>/",
        view=apps_filemanager_save_info,
        name="filemanager.save_info",
    ),
    path(
        r"filemanager/delete-dir/(?P<directory>.*)?/",
        view=apps_filemanager_delete_directory,
        name="filemanager.delete_dir",
    ),
    re_path(
        r"^filemanager/downloadfile/(?P<file_path>.+)$",
        view=apps_filemanager_download_file,
        name="filemanager.download_file",
    ),
    re_path(
        r"^filemanager/(?P<directory>.*)?/$",
        view=apps_filemanager,
        name="filemanager.detail",
    ),
    # Client Companies Url
    path(
        "client/companies/",
        view=apps_client_companies_list_view,
        name="client.companies",
    ),
    path(
        "client/details/<int:pk>",
        view=apps_client_details_companies_view,
        name="client.details",
    ),
    path(
        "client/locations/<int:pk>",
        view=apps_client_locations_view,
        name="client.locations",
    ),
    path(
        "client/locations_update/<int:pk>/<int:id>",
        view=apps_client_locations_update,
        name="client.locations_update",
    ),
    path(
        "client/locations_delete/<int:pk>/<int:id>",
        view=apps_client_locations_delete,
        name="client.locations_delete",
    ),
    path(
        "client/member_delete/<int:pk>/<int:id>",
        view=apps_client_member_delete,
        name="client.member_delete",
    ),
    path(
        "client/contacts/<int:pk>",
        view=apps_client_teammembers_view,
        name="client.contacts",
    ),
    path(
        "client/contacts/<int:pk>/<int:id>",
        view=apps_client_teammembers_update,
        name="client.contacts_update",
    ),
    path(
        "client/companies/<int:pk>",
        view=apps_client_companies_view,
        name="client.companies_details",
    ),
    path(
        "client/delete-companies/<int:pk>",
        view=apps_delete_client_companies_view,
        name="client.delete",
    ),
    path(
        "client/update_companies/<int:pk>",
        view=apps_update_client_companies_view,
        name="client.update_companies",
    ),
    # Invoices
    path(
        "invoices/webhook/",
        view=apps_invoices_create_webhook_view,
        name="invoices.webhook.create",
    ),
    path("invoices/list/", view=apps_invoices_list_view, name="invoices.list"),
    path(
        "invoices/details/<int:pk>",
        view=apps_invoices_details_view,
        name="invoices.details",
    ),
    path("invoices/create/", view=apps_invoices_create_view, name="invoices.create"),
    path("invoices/connect/", view=apps_invoices_connect_view, name="invoices.connect"),
    path("invoices/oauth/", view=apps_invoices_oauth_view, name="invoices.oauth"),
    path(
        "invoices/callback/", view=apps_invoices_callback_view, name="invoices.callback"
    ),
    path(
        "invoices/connected/",
        view=apps_invoices_connected_view,
        name="invoices.connected",
    ),
    path(
        "invoices/qbo_request/",
        view=apps_invoices_qbo_request_view,
        name="invoices.qbo_request",
    ),
    path("invoices/refresh/", view=apps_invoices_refresh_view, name="invoices.refresh"),
    path("invoices/revoke/", view=apps_invoices_revoke_view, name="invoices.revoke"),
    #  threshold
    path(
        "client/threshold/<int:pk>",
        view=apps_client_threshold_view,
        name="client.threshold",
    ),

    # Payment Pages
    path("todo/", view=apps_todo_view, name="todo"),
    path("api-key/", view=apps_api_key_view, name="api_key"),
]
