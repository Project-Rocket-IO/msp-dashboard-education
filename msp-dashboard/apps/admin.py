from django.contrib import admin
from .models import (
    QuickBooksToken,
    WebviewIntegrations,
    ClientUser,
    ClientWorkTypeRate,
    TicketList,
    ProjectList,
    ProjectComment,
    TicketComment,
    ClientCompany,
    TechnicianLabor,
    ClientTeamMembers,
    ClientLocations,
    Invoice,
    InvoiceItem,
    QuickBooksCustomer,
    QuickBooksInvoice,
)


@admin.register(TicketList)
class TicketListAdmin(admin.ModelAdmin):
    list_display = ["name", "create_date", "status", "client"]
    list_editable = ["status", "client"]
    list_filter = ["status"]

@admin.register(ProjectList)
class ProjectListAdmin(admin.ModelAdmin):
    list_display = ["name", "client", "status", "description", "create_date", "due_date"]
    list_editable = ["client", "status"]


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ["user"]


@admin.register(ProjectComment)
class ProjectCommentAdmin(admin.ModelAdmin):
    list_display = ["user"]


@admin.register(ClientCompany)
class ContactCompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "clients"]

    @admin.display(empty_value="???")
    def clients(self, obj):
        return list(obj.users.all())


@admin.register(TechnicianLabor)
class TechnicianLaborAdmin(admin.ModelAdmin):
    list_display = ["ticket", "created_at", "created_by", "minutes"]


@admin.register(ClientTeamMembers)
class ClientTeamMemberAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "work_email"]

@admin.register(ClientLocations)
class ClientLocationAdmin(admin.ModelAdmin):
    list_display = ["client", "email"]

# @admin.register(ContactCustomer)
# class ContactCustomerAdmin(admin.ModelAdmin):
#     list_display = ['name']

# @admin.register(Equipment)
# class EquipmentAdmin(admin.ModelAdmin):
#     list_display = ['model','serial']


@admin.register(ClientUser)
class ClientListAdmin(admin.ModelAdmin):
    list_display = [
        'company',
        'auth_user'
    ]


@admin.register(WebviewIntegrations)
class WebviewIntegrationsAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "url",
        "user"
    ]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["client", "id", "status", "created_at"]
    list_editable = ["status"]
    list_filter = ["status"]

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ["id", "invoice", "ticket", "hours", "description"]
    list_editable = ["hours", "description"]
    list_filter = ["invoice"]


@admin.register(QuickBooksToken)
class QuickBooksTokenAdmin(admin.ModelAdmin):
    list_display = ["mspcompany", "refresh_token", "realm_id"]


@admin.register(ClientWorkTypeRate)
class ClientWorkTypeRateAdmin(admin.ModelAdmin):
    list_display = ["client", "name", "rate"]
    list_editable = ["rate"]
    list_filter = ["client"]

@admin.register(QuickBooksCustomer)
class QuickBooksCustomerAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "email"]
    list_filter = ["name"]

@admin.register(QuickBooksInvoice)
class QuickBooksInvoiceAdmin(admin.ModelAdmin):
    list_display = ["id", "docNumber", "customer"]
    list_filter = ["customer"]

