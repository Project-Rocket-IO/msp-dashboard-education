import logging

from django.contrib.auth.backends import ModelBackend
from django.urls import reverse
from social_core.backends.azuread import AzureADOAuth2
from social_core.exceptions import AuthException
from social_core.utils import url_add_parameters

logger = logging.getLogger(__name__)


class TenantAwareAzureADOAuth2(AzureADOAuth2):
    """
    Tenant-aware Microsoft Entra ID backend.

    Each tenant uses its own Entra app registration and a fixed callback URL so
    the app registration can be configured once per tenant domain.
    """

    name = "azuread-oauth2"
    AUTHORIZATION_URL = "{base_url}/oauth2/v2.0/authorize"
    ACCESS_TOKEN_URL = "{base_url}/oauth2/v2.0/token"
    DEFAULT_SCOPE = ["openid", "profile", "email", "offline_access"]
    CALLBACK_URL_NAME = "entra_id_callback"

    def get_request(self):
        request = getattr(self.strategy, "request", None)
        if request is None:
            raise AuthException(self, "Request not available")
        return request

    def get_tenant_config(self):
        """Load Entra configuration from the current tenant."""
        request = self.get_request()
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            raise AuthException(self, "No tenant found in request")

        if not tenant.is_entra_id_configured:
            raise AuthException(
                self,
                "Entra ID authentication is not configured for this tenant",
            )

        return {
            "key": tenant.entra_id_client_id,
            "secret": tenant.entra_id_client_secret,
            "tenant_id": tenant.entra_id_tenant_id,
        }

    @property
    def tenant_id(self):
        return self.get_tenant_config()["tenant_id"]

    def get_key_and_secret(self):
        config = self.get_tenant_config()
        return config["key"], config["secret"]

    def get_redirect_uri(self, state=None):
        request = self.get_request()
        uri = request.build_absolute_uri(reverse(self.CALLBACK_URL_NAME))
        if self.REDIRECT_STATE and state:
            uri = url_add_parameters(uri, {"redirect_state": state})
        return uri

    def auth_extra_arguments(self):
        # Entra ID v2 uses OIDC scopes rather than the legacy `resource` param.
        return {}

    def refresh_token_params(self, token, *args, **kwargs):
        client_id, client_secret = self.get_key_and_secret()
        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": token,
            "grant_type": "refresh_token",
        }


class TenantAwareModelBackend(ModelBackend):
    """
    Custom model backend that ensures users belong to the current tenant.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username, password, **kwargs)

        if user and request and hasattr(request, "tenant"):
            if hasattr(user, "mspcompany") and user.mspcompany != request.tenant:
                logger.warning(
                    "User %s attempted to access tenant %s",
                    user.username,
                    request.tenant.company_name,
                )
                return None

        return user
