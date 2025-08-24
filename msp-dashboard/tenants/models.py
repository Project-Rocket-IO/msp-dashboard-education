from django.core.exceptions import ValidationError
from django_tenants.models import TenantMixin, DomainMixin
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import re
import uuid

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


class MyBaseModel(models.Model):
    optional_attrubite = {"null": True, "blank": True}

    address_1 = models.CharField(max_length=50)
    address_2 = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    zip = models.CharField(max_length=50)
    country = models.CharField(max_length=50, choices=COUNTRY_CHOICES)
    timezone = models.CharField(max_length=50)
    phone = models.CharField(**optional_attrubite, validators=[validate_phone_or_fax])
    fax = models.CharField(**optional_attrubite, validators=[validate_phone_or_fax])

    # Metadata
    class Meta:
        abstract = True

        # Methods

    def get_phone(self):
        if self.phone:
            return self.phone
        else:
            return self.company.phone

    def get_fax(self):
        if self.fax:
            return self.fax
        else:
            return self.company.fax


class MspCompany(MyBaseModel, TenantMixin):
    company_name = models.CharField(max_length=60)
    industry_type = models.CharField(max_length=68, choices=INDUSTRY_TYPE)
    email = models.EmailField(max_length=150, unique=True)
    owner_name = models.CharField(max_length=60, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    picture = models.ImageField(upload_to="images/company", blank=True, null=True)
    
    # Subscription fields
    subscription = models.ForeignKey('djstripe.Subscription',
                                   null=True,
                                   blank=True,
                                   help_text="The team's Stripe Subscription object, if it exists",
                                   on_delete=models.CASCADE
                                   )
    
    # Subscription tier (for easy access)
    SUBSCRIPTION_TIERS = (
        ('starter', 'Starter Tier'),
        ('growth', 'Growth Tier'),
        ('innovator', 'Innovator Tier'),
    )
    
    subscription_tier = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_TIERS,
        default='starter',
        help_text="Current subscription tier"
    )
    
    company_id = models.UUIDField(primary_key=True, default=uuid.uuid1, editable=False)
    
    # Entra ID (Azure AD) Configuration for External Clients
    enable_entra_id_auth = models.BooleanField(
        default=False,
        help_text="Enable Microsoft Entra ID (Azure AD) authentication for this tenant"
    )
    entra_id_tenant_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Client's Microsoft Entra ID Tenant ID (Directory ID)"
    )
    entra_id_client_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Client's Microsoft Entra ID Application (Client) ID"
    )
    entra_id_client_secret = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Client's Microsoft Entra ID Application Client Secret"
    )

    auto_create_schema = True

    # Metadata
    class Meta:
        pass
    
    def get_subscription_tier(self):
        """Get the current subscription tier"""
        # First check if we have a subscription_tier set
        if self.subscription_tier and self.subscription_tier != 'starter':
            return self.subscription_tier
        # Fallback to checking Stripe subscription
        if self.subscription and self.subscription.status == 'active':
            return self.subscription_tier
        return 'starter'
    
    def has_feature_access(self, feature):
        """Check if the company has access to a specific feature based on subscription tier"""
        tier = self.get_subscription_tier()
        
        # Feature access mapping
        feature_access = {
            'starter': ['dashboard', 'tickets', 'projects', 'clients', 'invoicing', 'calendar'],
            'growth': ['dashboard', 'tickets', 'projects', 'clients', 'invoicing', 'calendar', 'leads', 'sales'],
            'innovator': ['dashboard', 'tickets', 'projects', 'clients', 'invoicing', 'calendar', 'leads', 'sales', 'atlas']
        }
        
        return feature.lower() in feature_access.get(tier, [])


class Domain(DomainMixin):
    pass


@receiver(post_save, sender=MspCompany)
def create_company_directories(sender, instance, created, **kwargs):
    """
    Create directory structure for new MspCompany
    """
    if created:
        try:
            from apps.utils import create_tenant_directories
            # We need to temporarily set the tenant context
            from django_tenants.utils import tenant_context
            with tenant_context(instance):
                create_tenant_directories()
        except Exception as e:
            print(f"Error creating directories for company {instance.company_name}: {e}")
