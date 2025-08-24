from django.shortcuts import redirect
from django.contrib import messages
from django_tenants.utils import tenant_context
from django_otp.plugins.otp_email.models import EmailDevice
from django.contrib.auth import get_user_model
from django.views.generic import View
from django.urls import reverse

User = get_user_model()

class TenantAwareTwoFactorSetupView(View):
    """
    Custom 2FA setup view that ensures devices are created in the correct tenant context.
    """
    
    def get(self, request, *args, **kwargs):
        """Handle GET request for 2FA setup."""
        if not request.user.is_authenticated:
            return redirect('login')
        
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            messages.error(request, "No tenant context found.")
            return redirect('home')
        
        # Check if user already has 2FA enabled
        with tenant_context(tenant):
            existing_device = EmailDevice.objects.filter(user=request.user).first()
            if existing_device:
                messages.info(request, "Two-factor authentication is already enabled.")
                return redirect('two_factor:profile')
        
        # Redirect to the standard 2FA setup
        return redirect('two_factor:setup')
    
    def post(self, request, *args, **kwargs):
        """Handle POST request for 2FA setup."""
        if not request.user.is_authenticated:
            return redirect('login')
        
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            messages.error(request, "No tenant context found.")
            return redirect('home')
        
        # Create device in tenant context
        with tenant_context(tenant):
            try:
                # Check if device already exists
                existing_device = EmailDevice.objects.filter(user=request.user).first()
                if existing_device:
                    messages.info(request, "Two-factor authentication is already enabled.")
                    return redirect('two_factor:profile')
                
                # Create new device
                device = EmailDevice.objects.create(
                    user=request.user,
                    name='default',
                    confirmed=True
                )
                
                messages.success(request, "Two-factor authentication device created successfully.")
                return redirect('two_factor:setup')
                
            except Exception as e:
                messages.error(request, f"Error creating 2FA device: {str(e)}")
                return redirect('two_factor:setup')

def ensure_tenant_2fa_device(user, tenant):
    """
    Ensure a user has a 2FA device in the correct tenant context.
    """
    with tenant_context(tenant):
        # Check if device already exists
        existing_device = EmailDevice.objects.filter(user=user).first()
        if existing_device:
            return existing_device
        
        # Create new device
        device = EmailDevice.objects.create(
            user=user,
            name='default',
            confirmed=True
        )
        return device

def get_tenant_2fa_devices(user, tenant):
    """
    Get user's 2FA devices in the correct tenant context.
    """
    with tenant_context(tenant):
        return EmailDevice.objects.filter(user=user)
