from django.core.files import File as DjangoFile
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.conf import settings
from datetime import date
from django.db import models
from ckeditor.fields import RichTextField
from taggit.managers import TaggableManager
from accounts.models import MyBaseModel, TechnicianUser, MSPAuthUser
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
import random
import re
import os
import pytz

# Create your models here.

INVOICE_STATUS = (
    ("Pending", "Pending"),
    ("Paid", "Paid"),
    ("Overdue", "Overdue"),
)

API_CHOICES = (
    ("Apple", "Apple"),
    ("OpenAI", "OpenAI"),
    ("Google", "Google"),
    ("Other", "Other"),
)

EVENT_CHOICES = (
    ("Danger", "Danger"),
    ("Dark", "Dark"),
    ("Info", "Info"),
    ("Primary", "Primary"),
    ("Success", "Success"),
    ("Warning", "Warning"),
)

TAG_CHOICES = (
    ("Exiting", "Exiting"),
    ("Lead", "Lead"),
    ("Long-term", "Long-term"),
    ("Partner", "Partner"),
)

COUNTRY_CHOICES = (("United States", "United States"), ("Canada", "Canada"))

INDUSTRY_TYPE = (
    ("", "Select industry type"),
    ("Agriculture", "Agriculture"),
    ("Construction", "Construction"),
    ("Education", "Education"),
    ("Entertainment", "Entertainment"),
    ("Finance & Insurance", "Finance &  Insurance"),
    ("Healthcare", "Healthcare"),
    ("Higher Education", "Higher  Education"),
    ("Hospitality", "Hospitality"),
    ("Information Technology", "Information  Technology"),
    ("Manufacturing", "Manufacturing"),
    ("Nonprofit", "Nonprofit"),
    ("Professional Services", "Professional  Services"),
    ("Real Estate", "Real  Estate"),
    ("Retail", "Retail"),
    ("Telecommunications", "Telecommunications"),
    ("Transportation", "Transportation"),
    ("Utilities", "Utilities"),
    ("Wholesale", "Wholesale"),
)

STATUS_CHOICE = (
    ("Approved", "Approved"),
    ("New", "New"),
    ("Pending", "Pending"),
    ("Rejected", "Rejected"),
)

TYPE_CHOICE = (("Full Time", "Full Time"), ("Part Time", "Part Time"))

CONTRACT_STATUS = (
    ("Pending", "Pending"),
    ("Active", "Active"),
    ("Cancelled", "Cancelled"),
    ("Expired", "Expired"),
    ("Inactive", "Inactive"),
)

PAYMENT_METHOD = (
    ("Mastercard", "Mastercard"),
    ("Visa", "Visa"),
    ("COD", "COD"),
    ("Paypal", "Paypal"),
)

CUSTOMER_STATUS = (("Active", "Active"), ("Block", "Block"))

LABOR_INTERVAL = (
    ("6 Minute Intervals", "6 Minute Intervals"),
    ("15 Minute Intervals", "15 Minute Intervals"),
)


LABOR_TYPE = (
    ("6 Minute Intervals", "6 Minute Intervals"),
    ("15 Minute Intervals", "15 Minute Intervals"),
)


TICKET_STATUS = (
    ("New", "New"),
    ("In Progress", "In Progress"),
    ("Scheduled", "Scheduled"),
    ("Postponed", "Postponed"),
    ("Waiting on Client", "Waiting on Client"),
    ("Waiting on Vendor", "Waiting on Vendor"),
    ("Follow-Up", "Follow-Up"),
    ("Need to Post", "Need to Post"),
    ("Completed", "Completed"),
    ("Closed", "Closed"),
)

TIMEZONES = tuple(zip(pytz.all_timezones, pytz.all_timezones))

PROJECT_STATUS = (
    ("New", "New"),
    ("In Progress", "In Progress"),
    ("Scheduled", "Scheduled"),
    ("Follow Up", "Follow Up"),
    ("Reviewing", "Reviewing"),
    ("Observing", "Inprogress"),
    ("Waiting on Client", "Waiting on Client"),
    ("Waiting on Vendor", "Waiting on Vendor"),
    ("Waiting on Client", "Waiting on Client"),
    ("Postponed", "Postponed"),
    ("Post to Call Waiting", "Post to Call Waiting"),
    ("Completed", "Completed"),
)

PRIORITY = (
    ("Emergency", "Emergency"),
    ("High", "High"),
    ("Low", "Low"),
    ("Medium", "Medium"),
)

WORK_TYPE = (
    (10, "Default"),
    (15, "Hardware"),
    (20, "Network"),
    (25, "Software"),
)

SALES_CHOICES = (
    ("New Sale", "New Sale"),
    ("Proposal Created", "Proposal Created"),
    ("Proposal Sent", "Proposal Sent"),
    ("Proposal Executed", "Proposal Executed"),
    ("Sale Closed", "Sale Closed"),
)


OPTIONAL_ATTRIBUTE = {"null": True, "blank": True}


####################
# DEFAULT TO ADMIN #
####################
def set_admin_user():
    return MSPAuthUser.objects.get(is_superuser=True)


#################
## Validation ##
################


def validate_phone_or_fax(value):
    if value:
        phone_number_str = str(value)
        # Check if it's only the international code
        if re.match(r"^\+\d{1,4}$", phone_number_str):
            return
        # Optional: Further relaxed validations, e.g., length check (but not strict)
        digits_only = re.sub(
            r"\D", "", phone_number_str
        )  # Strip all non-numeric characters
        if (
            len(digits_only) < 10 or len(digits_only) > 15
        ):  # Basic length check for phone numbers
            raise ValidationError("Phone number or fax number seems incorrect.")


###############
# FILEPATH F(X)
###############
def ticket_directory_path(instance, filename):
    return tenant_ticket_directory_path(instance, filename)


def ticket_directory_files_path(instance, filename):
    return tenant_ticket_files_directory_path(instance, filename)


from apps.utils import (
    tenant_project_directory_path,
    tenant_project_files_directory_path,
    tenant_client_directory_path,
    tenant_client_files_directory_path,
    tenant_lead_directory_path,
    tenant_lead_files_directory_path,
    tenant_ticket_directory_path,
    tenant_ticket_files_directory_path,
    tenant_sales_directory_path,
    create_tenant_directories,
)

def project_directory_path(instance, filename):
    return tenant_project_directory_path(instance, filename)


def project_directory_files_path(instance, filename):
    return tenant_project_files_directory_path(instance, filename)


def client_directory_path(instance, filename):
    return tenant_client_directory_path(instance, filename)


def client_directory_files_path(instance, filename):
    return tenant_client_files_directory_path(instance, filename)


def lead_directory_path(instance, filename):
    return tenant_lead_directory_path(instance, filename)


def lead_files_directory_path(instance, filename):
    return tenant_lead_files_directory_path(instance, filename)


def filesystem_user_directory_path(instance, filename):
    return "filesystem/user_{0}/{1}".format(instance.user.user_id, filename)


#################
# DEFAULT IMAGE #


def random_img_clients():
    chosen_file = random.choice(
        os.listdir(f"{settings.STATICFILES_DIRS[0]}/images/default/clients")
    )
    img_path = f"/images/default/clients/{chosen_file}"
    return img_path


def random_img_leads():
    chosen_file = random.choice(
        os.listdir(f"{settings.STATICFILES_DIRS[0]}/images/default/leads")
    )
    img_path = f"/images/default/leads/{chosen_file}"
    return img_path


def random_img_projects():
    chosen_file = random.choice(
        os.listdir(f"{settings.STATICFILES_DIRS[0]}/images/default/projects")
    )
    img_path = f"/images/default/projects/{chosen_file}"
    return img_path


def random_img_tickets():
    chosen_file = random.choice(
        os.listdir(f"{settings.STATICFILES_DIRS[0]}/images/default/tickets")
    )
    img_path = f"/images/default/tickets/{chosen_file}"
    return img_path


def random_img_webviews():
    chosen_file = random.choice(
        os.listdir(f"{settings.STATICFILES_DIRS[0]}/images/default/webviews")
    )
    img_path = f"/images/default/webviews/{chosen_file}"
    return img_path


################
# Client User #


class ClientUser(models.Model):
    """Client User Model inheriting from MSPAuthUser."""

    company = models.ForeignKey(
        "apps.ClientCompany",
        related_name="users",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    auth_user = models.OneToOneField(
        MSPAuthUser, on_delete=models.CASCADE, related_name="client"
    )

    def clean(self):
        self.auth_user.clean()
        super().clean()

    def __str__(self):
        return str(self.auth_user.username)

    class Meta:
        verbose_name = "Client User"
        verbose_name_plural = "Client Users"
        unique_together = ("auth_user",)


################
# FILE HANDLER #


class File(object):
    file = None

    def file_name(self):
        if not self.file:
            return
        file_name = os.path.basename(self.file.name)
        return file_name

    def extension(self):
        if not self.file:
            return
        name, extension = os.path.splitext(self.file.name)
        if extension == ".pdf":
            return "PDF"
        if extension == ".txt":
            return "Text"
        if (
            extension == ".png"
            or extension == ".jpg"
            or extension == ".PNG"
            or extension == ".JPG"
        ):
            return "Image"
        if extension == ".csv":
            return "CSV"
        if extension == ".xlsx":
            return "Excel"
        if extension == ".doc":
            return "Word"
        if extension == ".mov":
            return "Video"
        if extension == ".zip":
            return "Zip File"
        return "other"

    def file_size(self):
        value = self.file.size
        if value < 512000:
            value = value / 1024.0
            ext = "KB"
        elif value < 4194304000:
            value = value / 1048576.0
            ext = "MB"
        else:
            value = value / 1073741824.0
            ext = "GB"
        return "%s %s" % (str(round(value, 2)), ext)


class TicketFiles(models.Model, File):
    ticket = models.ForeignKey(
        "TicketList", on_delete=models.CASCADE, null=True, blank=True
    )
    file = models.FileField(
        upload_to=ticket_directory_files_path, blank=True, null=True
    )
    upload_date = models.DateField(auto_now_add=True)


class TicketList(models.Model):
    logo = models.ImageField(upload_to=ticket_directory_path, blank=True, null=True)
    identifier = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    description = RichTextField(
        default="Add description for Ticket: ", null=True, blank=True
    )
    client = models.ForeignKey("ClientCompany", on_delete=models.CASCADE)
    assignment = models.ManyToManyField(TechnicianUser)
    create_date = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    end_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(blank=True, null=True)
    ticket_type = models.CharField(
        max_length=50, choices=TYPE_CHOICE, null=True, blank=True
    )
    status = models.CharField(max_length=50, choices=TICKET_STATUS)
    priority = models.CharField(max_length=10, choices=PRIORITY, null=True, blank=True)
    project = models.ForeignKey(
        "ProjectList", on_delete=models.SET_NULL, blank=True, null=True
    )
    tag = TaggableManager(blank=True)
    files = models.FileField(upload_to=ticket_directory_path, blank=True, null=True)
    # slug = models.SlugField(max_length=50)
    # labor = models.ForeignKey(TechnicianLabor,
    #     on_delete=models.CASCADE,
    #     default="Pick Labor"
    # )

    # Metadata
    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ["-identifier"]
        permissions = [
            ("view_own_ticketlist", "Can view own tickets"),
            ("view_ticket_stats", "Can view ticket statistics"),
            ("view_estimated_work", "Can view estimated work"),
            ("assign_own_ticketlist", "Can assign themselves to a ticket"),
            ("assign_other_ticket", "Can assign others to a ticket"),
            ("complete_ticketlist", "Can mark a ticket as Completed"),
            ("close_ticketlist", "Can mark a ticket as Closed"),
        ]

    # Methods
    @property
    def days_until(self):
        if self.due_date:
            date_diff = self.due_date - date.today()
            day_until = date_diff.days
        else:
            day_until = 0
        return day_until

    @property
    def identifier_thousand(self):
        thousand = self.identifier + 1000
        return thousand

    # def get_photo_url(self):
    #     if self.logo and hasattr(self.logo, "url"):
    #         return self.logo.url
    #     else:
    #         return "/static/images/galaxy/img-1.jpg"

    @property
    def get_photo_url(self):
        if self.logo:
            return self.logo.url
        # First time rendering will save a default image
        if not self.logo:
            picture_path = random_img_tickets()
            picture_path = settings.STATICFILES_DIRS[0] + picture_path
            self.logo.save(
                os.path.basename(picture_path), DjangoFile(open(picture_path, "rb"))
            )
        return self.logo.url

    def get_difference_time(self):
        """Returns Metrics from models."""
        return self.start - self.end

    def __str__(self):
        """String for representing the MyModelName object (in Admin site etc.)."""
        return self.name


class ProjectFiles(models.Model, File):
    history = AuditlogHistoryField()
    project = models.ForeignKey(
        "ProjectList", on_delete=models.CASCADE, null=True, blank=True
    )
    file = models.FileField(
        upload_to=project_directory_files_path, blank=True, null=True
    )
    upload_date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Project File"
        verbose_name_plural = "Project Files"
        ordering = ["-upload_date"]


class ProjectList(models.Model):
    history = AuditlogHistoryField()
    identifier = models.AutoField(primary_key=True)
    logo = models.ImageField(upload_to=project_directory_path, blank=True, null=True)
    name = models.CharField(max_length=50)
    client = models.ForeignKey("ClientCompany", on_delete=models.CASCADE)
    description = RichTextField(
        default="Please add Project description... ", null=True, blank=True
    )
    create_date = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    end_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    assignment = models.ManyToManyField(TechnicianUser)
    tickets = models.ManyToManyField("TicketList", blank=True, related_name="projects")
    status = models.CharField(
        max_length=50, choices=PROJECT_STATUS, blank=True, null=True
    )
    priority = models.CharField(max_length=10, choices=PRIORITY, null=True, blank=True)
    tag = TaggableManager(blank=True)

    # Metadata
    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ["-name"]
        permissions = [
            ("view_own_projects", "Can view their own projects"),
            # ("view_estimated_work", "Can view estimated work"),
            ("assign_own_project", "Can assign themselves to a project"),
            ("assign_other_project", "Can assign others to a project"),
        ]

    # Methods
    # def get_absolute_url(self):
    #     """Returns the URL to access a particular instance of MyModelName."""
    #     return reverse('model-detail-view', args=[str(self.id)])
    # def get_photo_url(self):
    #     if self.logo and hasattr(self.logo, "url"):
    #         return self.logo.url
    #     else:
    #         return "/static/images/galaxy/img-1.jpg"

    @property
    def get_photo_url(self):
        if self.logo:
            return self.logo.url
        # First time rendering will save a default image
        if not self.logo:
            picture_path = random_img_projects()
            picture_path = settings.STATICFILES_DIRS[0] + picture_path
            self.logo.save(
                os.path.basename(picture_path), DjangoFile(open(picture_path, "rb"))
            )
        return self.logo.url

    @property
    def identifier_thousand(self):
        thousand = self.identifier + 1000
        return thousand

    def __str__(self):
        """String for representing the MyModelName object (in Admin site etc.)."""
        return self.name


class TicketComment(models.Model):
    user = models.ForeignKey(
        MSPAuthUser, blank=True, null=True, on_delete=models.CASCADE
    )
    date_added = models.DateTimeField(auto_now_add=True)
    ticket = models.ForeignKey(
        TicketList, blank=True, null=True, on_delete=models.CASCADE
    )
    body = models.TextField()
    private = models.BooleanField(default=False)

    def __str__(self):
        return "%s -%s" % (self.body, self.date_added)

    class Meta:
        verbose_name = "Ticket Comment"
        verbose_name_plural = "Ticket Comments"
        ordering = ["-date_added"]
        permissions = [
            ("view_own_ticket_comments", "Can view their own ticket comments"),
            ("delete_own_ticket_comments", "Can delete their own ticket comments"),
        ]


class TicketCommentReplies(models.Model):
    user = models.ForeignKey(
        MSPAuthUser, blank=True, null=True, on_delete=models.CASCADE
    )
    ticket = models.ForeignKey(
        TicketList, blank=True, null=True, on_delete=models.CASCADE
    )
    date_added = models.DateTimeField(auto_now_add=True)
    body = models.TextField()
    private = models.BooleanField(default=False)
    comment = models.ForeignKey(
        TicketComment, blank=True, null=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return "%s -%s" % (self.body, self.date_added)

    class Meta:
        verbose_name = "Ticket Comment Reply"
        verbose_name_plural = "Ticket Comment Replies"
        ordering = ["-date_added"]
        permissions = [
            (
                "view_own_ticket_comments_replies",
                "Can view their own ticket comments replies",
            ),
            (
                "delete_own_ticket_comments_replies",
                "Can delete their own ticket comments replies",
            ),
        ]


class ProjectComment(models.Model):
    project = models.ForeignKey(ProjectList, on_delete=models.CASCADE)
    user = models.ForeignKey(
        MSPAuthUser, on_delete=models.CASCADE, blank=True, null=True
    )
    body = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    private = models.BooleanField(default=False)

    def __str__(self):
        return "%s -%s" % (self.project.name, self.user)

    class Meta:
        verbose_name = "Project Comment"
        verbose_name_plural = "Project Comments"
        ordering = ["-date_added"]
        permissions = [
            ("view_own_project_comments", "Can view their own project comments"),
            ("delete_own_project_comments", "Can delete their own project comments"),
        ]


class ProjectCommentReplies(models.Model):
    user = models.ForeignKey(
        MSPAuthUser, blank=True, null=True, on_delete=models.CASCADE
    )
    project = models.ForeignKey(
        ProjectList, blank=True, null=True, on_delete=models.CASCADE
    )
    date_added = models.DateTimeField(auto_now_add=True)
    body = models.TextField()
    private = models.BooleanField(default=False)
    comment = models.ForeignKey(
        ProjectComment, blank=True, null=True, on_delete=models.DO_NOTHING
    )

    def __str__(self):
        return "%s -%s" % (self.body, self.date_added)

    class Meta:
        verbose_name = "Project Comment Reply"
        verbose_name_plural = "Project Comment Replies"
        ordering = ["-date_added"]
        permissions = [
            (
                "view_own_project_comment_replies",
                "Can view their own project comment replies",
            ),
            (
                "delete_own_project_comments_replies",
                "Can delete their own project comments replies",
            ),
        ]


class ClientCompanyFiles(models.Model, File):
    client = models.ForeignKey(
        "ClientCompany", on_delete=models.CASCADE, null=True, blank=True
    )
    file = models.FileField(
        upload_to=client_directory_files_path, blank=True, null=True
    )
    upload_date = models.DateField(auto_now_add=True)


class ClientCompany(MyBaseModel, models.Model):
    logo = models.ImageField(
        upload_to=client_directory_path,
        blank=True,
        null=True,
    )
    threshold = models.IntegerField(default=0)
    name = models.CharField(max_length=150)
    contact_first = models.CharField(max_length=50)
    contact_last = models.CharField(max_length=50)
    industry = models.CharField(
        max_length=50, choices=INDUSTRY_TYPE, blank=True, null=True
    )
    website = models.URLField(max_length=150, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email = models.EmailField(max_length=150, unique=True)
    main_tech = models.ForeignKey(TechnicianUser, on_delete=models.SET_NULL, null=True, blank=True)
    # In case if we need subscription based invoicing, we can use models.PROTECT to still keep the client even if Quickbooks Customer is deleted
    # For example, the MSPs were to cancel a subscription of invoicing, we can still keep the client and the client's data. But then we don't need Quickbooks Customer
    # Remember, Quickbooks Customer was only needed or invoicing purposes.
    quickbooks_customer = models.OneToOneField(
        "QuickBooksCustomer",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="msp_client",
    )
    # MSPD Running Invoice
    quickbooks_invoice = models.OneToOneField(
        "QuickBooksInvoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="msp_client",
    )

    class Meta:
        verbose_name_plural = "Crm Companies"

    @property
    def main_tech_object(self):
        #! This is a hack to get the main tech for the client if it's not set or got deleted
        if self.main_tech:
            return self.main_tech
        else:
            return TechnicianUser.objects.first()

    @property
    def get_photo_url(self):
        
        if bool(self.logo):
            return self.logo.url
        else:
            return os.path.join(settings.STATIC_URL, "images/users/multi-user.jpg")

    def __str__(self):
        return self.name if self.name else repr(self)


@receiver(post_save, sender=ClientCompany)
def create_client_invoice(sender, instance, created, **kwargs):
    """
    Signal to create an invoice when a client company is created.
    Only creates an invoice if this is a new client (created=True)
    Also makes sure that the invoice doesn't exist already
    """
    # Check if the invoice already exists, in case it was created from the webhook
    if Invoice.objects.filter(client=instance).exists():
        return

    # Create the invoice
    if created:
        invoice = Invoice(client=instance, status="Pending")
        
        # Only set quickbooks invoice data if it exists
        if instance.quickbooks_invoice:
            invoice.id = instance.quickbooks_invoice.id
            invoice.amount = instance.quickbooks_invoice.amount
            invoice.amount_paid = instance.quickbooks_invoice.amount_paid
        
        invoice.save()


@receiver(post_delete, sender=ClientCompany)
def delete_client_company_invoice(sender, instance, **kwargs):
    """
    Signal to delete an invoice when a client company is deleted.
    """
    if Invoice.objects.filter(client=instance).exists():
        Invoice.objects.filter(client=instance).delete()


class QuickBooksCustomer(models.Model):
    """Model to store QuickBooks customer data"""

    id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "QuickBooks Customer"
        verbose_name_plural = "QuickBooks Customers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name}"


class QuickBooksInvoice(models.Model):
    """Model to store QuickBooks invoice data"""

    id = models.CharField(max_length=255, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(
        QuickBooksCustomer, on_delete=models.CASCADE, null=True, blank=True
    )
    docNumber = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "QuickBooks Invoice"
        verbose_name_plural = "QuickBooks Invoices"
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.docNumber} - {str(self.customer)}"


class ClientWorkTypeRate(models.Model):
    client = models.ForeignKey(
        ClientCompany, on_delete=models.CASCADE, related_name="work_type_rates"
    )
    name = models.CharField(max_length=255)  # software, hardware, etc.
    rate = models.DecimalField(max_digits=10, decimal_places=2)  # $20, $30, etc.

    def __str__(self):
        return f"{self.client.name} - {self.name}"

    class Meta:
        verbose_name = "Client Work Type Rate"
        verbose_name_plural = "Client Work Type Rates"
        unique_together = ("client", "name")


class ClientLocations(models.Model):
    client = models.ForeignKey(ClientCompany, on_delete=models.CASCADE)
    headquarter = models.BooleanField(null=True, blank=True, default=False)
    name = models.CharField(max_length=255)
    address_1 = models.CharField(max_length=80)
    address_2 = models.CharField(max_length=10, null=True, blank=True)
    city = models.CharField(max_length=25)
    state = models.CharField(max_length=33)
    phone = models.CharField(**OPTIONAL_ATTRIBUTE, validators=[validate_phone_or_fax])
    email = models.EmailField(max_length=150)
    zip = models.CharField(max_length=10)

    # Metadata
    class Meta:
        verbose_name = "Client Location"
        verbose_name_plural = "Client Locations"
        ordering = ["-client"]

    def __str__(self):
        return f"CL {self.name}"


class ClientTeamMembers(models.Model):
    location = models.ForeignKey(
        ClientLocations, on_delete=models.SET_NULL, blank=True, null=True
    )
    client = models.ForeignKey(ClientCompany, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=25)
    last_name = models.CharField(max_length=25)
    title = models.CharField(max_length=25, blank=True, null=True)
    work_phone = models.CharField(
        **OPTIONAL_ATTRIBUTE, validators=[validate_phone_or_fax]
    )
    work_email = models.EmailField(max_length=150)
    location = models.CharField(max_length=255, null=True, blank=True)

    # Metadata
    class Meta:
        verbose_name = "Client Team Member"
        verbose_name_plural = "Client Team Members"
        ordering = ["-first_name"]

    def __str__(self):
        return f"CT {self.first_name} {self.last_name}"


#######################
# SALES
#######################


class SalesRequests(models.Model):
    name = models.CharField(max_length=50)
    client = models.ForeignKey(ClientCompany, on_delete=models.CASCADE)
    type = models.CharField(max_length=45, choices=SALES_CHOICES)
    value = models.FloatField(default=0.00)
    owner = models.ForeignKey(TechnicianUser, on_delete=models.CASCADE)
    contact = models.ForeignKey(
        ClientTeamMembers, on_delete=models.SET_NULL, null=True, blank=True
    )
    due_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    create_date = models.DateField(auto_now_add=True)

    # Metadata
    class Meta:
        ordering = ["-create_date"]


#######################
# FILEMANAGER
#######################


class FileInfo(models.Model):
    path = models.URLField()
    info = models.CharField(max_length=255)

    def __str__(self):
        return self.path

    def file_size(self):
        return os.path.getsize(self.path)


#########################
# MSP LEAD
#########################


class LeadFiles(models.Model, File):
    history = AuditlogHistoryField()
    lead = models.ForeignKey(
        "LeadCompany", on_delete=models.CASCADE, null=True, blank=True
    )
    file = models.FileField(upload_to=lead_files_directory_path, blank=True, null=True)
    upload_date = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Lead File"
        verbose_name_plural = "Lead Files"
        ordering = ["-upload_date"]


class LeadCompany(MyBaseModel, models.Model):
    history = AuditlogHistoryField()
    logo = models.ImageField(
        upload_to=lead_directory_path, default=random_img_leads, blank=True, null=True
    )
    name = models.CharField(max_length=150)
    contact_first = models.CharField(max_length=50)
    contact_last = models.CharField(max_length=50)
    industry = models.CharField(
        max_length=50, choices=INDUSTRY_TYPE, blank=True, null=True
    )
    website = models.URLField(max_length=150, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email = models.EmailField(max_length=150, unique=True)
    score = models.IntegerField(blank=True, null=True)
    assignment = models.ForeignKey(
        TechnicianUser, blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Lead Company"
        verbose_name_plural = "Leads Companies"
        ordering = ["-date_added"]

    @property
    def get_photo_url(self):
        if self.logo and hasattr(self.logo, "url"):
            return self.logo.url
        else:
            return "/static/images/users/multi-user.jpg"


class LeadOpportunity(models.Model):
    history = AuditlogHistoryField()
    lead = models.ForeignKey("LeadCompany", on_delete=models.CASCADE)
    first_contact = models.DateField()
    created_by = models.ForeignKey(
        TechnicianUser, on_delete=models.SET(set_admin_user), related_name="creator"
    )
    assigned_to = models.ForeignKey(
        TechnicianUser,
        on_delete=models.SET(set_admin_user),
        related_name="maintainer",
    )
    attempts = models.IntegerField(default=0)
    conversion_rate = models.FloatField(default=0.0)
    promo = models.TextField()
    converted_date = models.DateField(null=True, blank=True)
    update_date = models.DateField(auto_now=True)
    create_date = models.DateField(auto_now_add=True)

    # Metadata
    class Meta:
        verbose_name = "Lead Opportunity"
        verbose_name_plural = "Lead Opportunities"
        ordering = ["-lead"]


#########################
# TECHNICIAN LABOR
#########################


class TechnicianLabor(models.Model):
    ticket = models.ForeignKey(
        TicketList, on_delete=models.CASCADE, related_name="technician_labor"
    )
    minutes = models.BigIntegerField(default=0)
    is_tracked = models.BooleanField(default=False)
    created_by = models.ForeignKey(TechnicianUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    comment = models.TextField(blank=True, null=True)
    # intervals = models.CharField(max_length=75, choices=LABOR_INTERVAL)

    # Metadata
    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("view_labor_stats", "Can view labor statistics"),
        ]

    # Methods
    # def get_difference_time(self):
    #     """Returns Metrics from models."""
    #     return self.created_at

    def __str__(self):
        """String for representing the MyModelName object (in Admin site etc.)."""
        if self.ticket:
            return "%s - %s" % (self.ticket.name, self.created_at)

        return "%" % self.created_at


##################
# Invoices
##################


# One and only one invoice per client
class Invoice(models.Model):
    """
    Invoice model

    It's a running invoice, and we just keep adding more and more invoice items to it.
    """

    client = models.ForeignKey(ClientCompany, on_delete=models.CASCADE)
    status = models.CharField(max_length=255, choices=INVOICE_STATUS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Invoice {self.id} for {self.client.name}"

    @property
    def amount_charged(self):
        total_amount = 0
        # Get all closed tickets for this client
        closed_tickets = self.client.ticketlist_set.filter(status="Closed")

        for ticket in closed_tickets:
            # Get total minutes for this ticket
            total_minutes = (
                ticket.technician_labor.aggregate(total_minutes=Sum("minutes"))[
                    "total_minutes"
                ]
                or 0
            )
            # Convert to hours
            hours = total_minutes / 60

            # work_type field has been removed - no rate calculation
            # ticket_amount = 0
            # total_amount += ticket_amount

        return total_amount

    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        ordering = ["-created_at"]


# One or more invoice items per invoice
class InvoiceItem(models.Model):
    """
    Invoice item model
    """

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    ticket = models.ForeignKey(
        TicketList, on_delete=models.CASCADE, related_name="invoice_items"
    )
    description = models.TextField(blank=True, null=True)
    hours = models.IntegerField(default=0)  # calculated from ticket labor

    def clean(self):
        # Make sure the ticket is closed before creating an invoice item
        if self.ticket and self.ticket.status != "Closed":
            raise ValidationError("Only closed tickets can be added to invoices.")

        # Make sure the ticket is not already in an invoice item of the same invoice
        if (
            self.ticket
            and self.ticket.invoice_items.filter(invoice=self.invoice).exists()
        ):
            raise ValidationError(
                "Ticket is already in an invoice item of the same invoice."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice item {self.id} for {self.invoice.client.name}"

    class Meta:
        verbose_name = "Invoice Item"
        verbose_name_plural = "Invoice Items"


#########################
# WEBVIEW INTEGRATIONS
#########################


class WebviewIntegrations(models.Model):
    url = models.CharField(max_length=255)
    name = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(
        MSPAuthUser, on_delete=models.CASCADE, null=True, blank=True
    )
    picture = models.ImageField(
        upload_to="images/webview", default=random_img_webviews, blank=True, null=True
    )
    favorite = models.BooleanField(default=False)
    created_date = models.DateField(auto_now_add=True)

    def get_photo_url(self):
        if self.picture and hasattr(self.picture, "url"):
            return self.picture.url
        else:
            return "/static/images/galaxy/img-1.png"

    @property
    def get_url(self):
        if self.url.startswith("http"):
            return self.url
        return "https://" + self.url


##################
# API INTEGRATIONS
##################


class APIIntegrations(models.Model):
    key = models.CharField(max_length=255)
    name = models.CharField(max_length=25)
    type = models.CharField(max_length=30, choices=API_CHOICES, blank=True, null=True)
    date_added = models.DateField(auto_now_add=True)

    # Metadata
    class Meta:
        verbose_name = "API Integration"
        verbose_name_plural = "API Integrations"
        ordering = ["-name"]


##################
# API INTEGRATIONS
##################
auditlog.register(LeadCompany)
auditlog.register(ProjectList)
auditlog.register(ProjectFiles)
auditlog.register(LeadOpportunity)
auditlog.register(LeadFiles)

# class ContactCompany(MyBaseModel, models.Model):
#     industry = models.CharField(max_length=150, choices=INDUSTRY_TYPE)
#     email = models.EmailField(max_length=150, unique=True)
#     description = models.TextField(default=f"Add {MyBaseModel.name} description")
#     main_tech = models.ForeignKey(TechnicianUser, on_delete=models.CASCADE)
#     picture = models.ImageField(upload_to='images/clientcompany',blank=True,null=True)
#     company_id = models.UUIDField(
#         primary_key = True,
#         default = uuid.uuid4,
#         editable = False
#     )

#     created_date = models.DateField()

#     # Metadata
#     class Meta:
#         pass

#     # Methods
#     def get_photo_url(self):
#         if self.picture and hasattr(self.picture, 'url'):
#             return self.picture.url
#         else:
#             return "/static/images/users/user-dummy-img.jpg"

#     def __str__(self):
#         """String for representing the MyModelName object (in Admin site etc.)."""
#         return self.name


# class ContactCustomer(MyBaseModel, models.Model):
#     main_contact = models.BooleanField(default=False)
#     email = models.EmailField(max_length=150,unique=True, null=True)
#     company = models.ForeignKey(ContactCompany, on_delete=models.CASCADE)
#     picture = models.ImageField(upload_to='images/client',blank=True,null=True)

#     # Metadata
#     class Meta:
#         pass

#     # Methods
#     def get_photo_url(self):
#         if self.picture and hasattr(self.picture, 'url'):
#             return self.picture.url
#         if self.company.picture and hasattr(self.picture, 'url'):
#             return self.company.picture.url
#         else:
#             return "/static/images/users/user-dummy-img.jpg"

#     def __str__(self):
#         """String for representing the MyModelName object (in Admin site etc.)."""
#         return self.name


# class Equipment(models.Model):
#     manufacturer = models.CharField(max_length=50)
#     model = models.CharField(max_length=50)
#     serial = models.IntegerField()
#     reference = models.IntegerField()
#     description = models.TextField(default="description")
#     service_next = models.DateField()
#     service_last = models.DateField()
#     installed_date = models.DateField()
#     purchase_date = models.DateField()
#     purchase_location = models.CharField(max_length=200)
#     warranty_exp = models.DateField()
#     item_type = models.CharField(max_length=15,choices=TYPE_CHOICE)

#         # Metadata
#     class Meta:
#         ordering = ['-model']

#     # Methods
#     def get_difference_time(self):
#         """Returns Metrics from models."""
#         return self.start - self.end

#     def __str__(self):
#         """String for representing the MyModelName object (in Admin site etc.)."""
#         return self.model

# class StripeSubscription(models.Model):
#     start_date = models.DateTimeField(help_text="The start date of the subscription.")
#     status = models.CharField(max_length=20, help_text="The status of this subscription.")
#     # other data we need about the Subscription from Stripe goes here


# class MyStripeModel(models.Model):
#     name = models.CharField(max_length=100)
#     stripe_subscription = models.ForeignKey(StripeSubscription, on_delete=models.CASCADE)

from django.utils import timezone
from datetime import timedelta
from django.db.models import Count


def get_tickets_worked_on():
    today = timezone.now().date()
    last_week = today - timedelta(days=6)
    last_month = today - timedelta(days=30)
    last_6m = today - timedelta(days=365)
    last_year = today - timedelta(days=365)

    last_week_tickets = (
        TechnicianLabor.objects.filter(created_at__gte=last_week, created_at__lte=today)
        .values("ticket")
        .annotate(count=Count("ticket"))
        .count()
    )
    last_month_tickets = (
        TechnicianLabor.objects.filter(
            created_at__gte=last_month, created_at__lte=today
        )
        .values("ticket")
        .annotate(count=Count("ticket"))
        .count()
    )
    last_6m_tickets = (
        TechnicianLabor.objects.filter(created_at__gte=last_6m, created_at__lte=today)
        .values("ticket")
        .annotate(count=Count("ticket"))
        .count()
    )
    last_year_tickets = (
        TechnicianLabor.objects.filter(created_at__gte=last_year, created_at__lte=today)
        .values("ticket")
        .annotate(count=Count("ticket"))
        .count()
    )

    return {
        "last_week": last_week_tickets,
        "last_month": last_month_tickets,
        "last_6m": last_6m_tickets,
        "last_year": last_year_tickets,
    }


# # class ContractAgreement(models.Model):
# #     name = models.CharField(max_length=50)
# #     status = models.CharField(max_length=30, choices=CONTRACT_STATUS)
# #     start_date = models.DateField(blank=True, null=True)
# #     expiration_date = models.DateField(blank=True, null=True)
# #     contract_type = models.CharField(max_length=50)
# #     contract_number = models.CharField(max_length=50)
# #     po_number = models.CharField(max_length=50)
# #     hidden = models.BooleanField()
# #     customer = models.ForeignKey(ContactCompany, on_delete=models.SET_NULL)
# #     limit =
# #     overage =
# #     tax_code =
# #     description = models.TextField(blank=True)
# #     hrly_rate = models.CharField(max_length=75, choices=LABOR_INTERVAL)
# #     initial_rate = models.DateField(blank=True, null=True)
# #     threshold = models.IntegerField()
# #     refurb_hrs = models.CharField(max_length=45, choices=LABOR_TYPE)
# #     refurb_log = models.DateField(blank=True)
# #     company =


from tenants.models import MspCompany


class QuickBooksToken(models.Model):
    mspcompany = models.OneToOneField(MspCompany, on_delete=models.CASCADE)
    refresh_token = models.CharField(max_length=1000)
    realm_id = models.CharField(max_length=1000, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_in = models.IntegerField(default=0)
    # This field will be used for the 1 day expiry of access token (only for the development environment)
    # Because I don't have celery running 24/7 here on my local machine.
    # However, we don't need this field in an actual production environment.
    # But just to be safe. We'll use this whenever there's a failed request to QB.
    # We'll set this field to False whenever there's a failed request to QB.
    is_refresh_token_replaced = models.BooleanField(default=False)

    class Meta:
        verbose_name = "QuickBooks Token"
        verbose_name_plural = "QuickBooks Tokens"
        ordering = ["-created_at"]

    @property
    def is_refresh_token_valid(self):
        return self.updated_at + timedelta(seconds=self.expires_in) > timezone.now()

    def __str__(self):
        return f"{self.mspcompany.company_name} - {self.realm_id}"
