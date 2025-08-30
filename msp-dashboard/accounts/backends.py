from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django_tenants.utils import get_tenant
from social_core.backends.azuread import AzureADOAuth2
from social_core.exceptions import AuthException
from django_tenants.utils import tenant_context
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class TenantAwareAzureADOAuth2(AzureADOAuth2):
    """
    Custom Azure AD OAuth2 backend for external client Entra ID authentication
    Each tenant uses their own Azure AD configuration
    """
    name = 'azuread-oauth2'
    
    def get_tenant_config(self):
        """Get Entra ID configuration from the current tenant"""
        try:
            # Get tenant from request
            if not hasattr(self, 'request') or not self.request:
                raise AuthException(self, "Request not available")
            
            tenant = getattr(self.request, 'tenant', None)
            if not tenant:
                raise AuthException(self, "No tenant found in request")
            
            # Check if Entra ID is enabled for this tenant
            if not tenant.enable_entra_id_auth:
                raise AuthException(self, "Entra ID authentication is not enabled for this tenant")
            
            # Check if all required fields are configured
            if not tenant.entra_id_tenant_id:
                raise AuthException(self, "Entra ID Tenant ID is not configured for this tenant")
            
            if not tenant.entra_id_client_id:
                raise AuthException(self, "Entra ID Client ID is not configured for this tenant")
            
            if not tenant.entra_id_client_secret:
                raise AuthException(self, "Entra ID Client Secret is not configured for this tenant")
            
            return {
                'key': tenant.entra_id_client_id,
                'secret': tenant.entra_id_client_secret,
                'tenant_id': tenant.entra_id_tenant_id,
            }
        except Exception as e:
            logger.error(f"Error getting tenant Entra ID config: {e}")
            raise AuthException(self, "Entra ID configuration not found")
    
    def get_key_and_secret(self):
        """Use global configuration from settings"""
        config = self.get_tenant_config()
        return config['key'], config['secret']
    
    def authorization_url(self):
        """Use global tenant ID from settings"""
        config = self.get_tenant_config()
        tenant_id = config['tenant_id']
        
        return (
            f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize',
            {
                'client_id': config['key'],
                'response_type': 'code',
                'scope': ' '.join(self.get_scope()),
                'redirect_uri': self.get_redirect_uri(),
            }
        )
    
    def access_token_url(self):
        """Use global tenant ID from settings"""
        config = self.get_tenant_config()
        tenant_id = config['tenant_id']
        return f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'


class TenantAwareModelBackend(ModelBackend):
    """
    Custom model backend that ensures users belong to the current tenant
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username, password, **kwargs)
        
        if user and hasattr(request, 'tenant'):
            # Ensure the user belongs to the current tenant
            # This is a basic check - you might want to add more sophisticated tenant-user relationships
            if hasattr(user, 'mspcompany') and user.mspcompany != request.tenant:
                logger.warning(f"User {user.username} attempted to access tenant {request.tenant.company_name}")
                return None
        
        return user
