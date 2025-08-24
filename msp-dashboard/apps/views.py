from django_tenants.utils import tenant_context
from django_otp.plugins.otp_email.models import EmailDevice
from django.contrib.auth import get_user_model

User = get_user_model()

class TenantAwareTwoFactorSetupView:
    """
    Custom 2FA setup view that ensures devices are created in the correct tenant context.
    """
    
    @staticmethod
    def create_email_device(user, tenant):
        """
        Create an email device for a user in the correct tenant context.
        """
        with tenant_context(tenant):
            # Check if device already exists
            existing_device = EmailDevice.objects.filter(user=user).first()
            if existing_device:
                return existing_device
            
            # Create new device in tenant context
            device = EmailDevice.objects.create(
                user=user,
                name='default',
                confirmed=True
            )
            return device
    
    @staticmethod
    def get_user_devices(user, tenant):
        """
        Get user's 2FA devices in the correct tenant context.
        """
        with tenant_context(tenant):
            return EmailDevice.objects.filter(user=user)
