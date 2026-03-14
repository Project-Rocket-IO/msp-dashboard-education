from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import reverse
from social_django.utils import load_backend, load_strategy

from accounts.views import entra_id_begin
from tenants.models import MspCompany


@override_settings(ALLOWED_HOSTS=["assumption.rocket-command.com", ".rocket-command.com"])
class TenantAwareAzureADOAuth2Tests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = MspCompany(
            company_name="Assumption",
            schema_name="assumption",
            enable_entra_id_auth=True,
            entra_id_tenant_id="tenant-guid",
            entra_id_client_id="client-guid",
            entra_id_client_secret="secret-value",
        )

    def build_request(self, path="/oauth2/login/entra-id/"):
        request = self.factory.get(
            path,
            secure=True,
            HTTP_HOST="assumption.rocket-command.com",
        )
        request.session = {}
        request.user = AnonymousUser()
        request.tenant = self.tenant
        return request

    def build_backend(self):
        request = self.build_request()
        strategy = load_strategy(request)
        return load_backend(
            strategy,
            "azuread-oauth2",
            redirect_uri=reverse("social:complete", args=("azuread-oauth2",)),
        )

    def test_entra_id_ready_requires_core_fields(self):
        self.assertTrue(self.tenant.is_entra_id_configured)

        incomplete = MspCompany(
            company_name="Assumption",
            schema_name="assumption",
            enable_entra_id_auth=True,
            entra_id_tenant_id="tenant-guid",
        )
        self.assertFalse(incomplete.is_entra_id_configured)

    def test_backend_uses_custom_callback_url(self):
        backend = self.build_backend()
        self.assertEqual(
            backend.get_redirect_uri(),
            "https://assumption.rocket-command.com/oauth2/callback",
        )

    def test_backend_uses_tenant_specific_v2_endpoint(self):
        backend = self.build_backend()
        auth_url = backend.auth_url()
        parsed = urlparse(auth_url)
        query = parse_qs(parsed.query)

        self.assertEqual(parsed.netloc, "login.microsoftonline.com")
        self.assertEqual(parsed.path, "/tenant-guid/oauth2/v2.0/authorize")
        self.assertEqual(query["client_id"], ["client-guid"])
        self.assertEqual(
            query["redirect_uri"],
            ["https://assumption.rocket-command.com/oauth2/callback"],
        )
        self.assertIn("openid", query["scope"][0])
        self.assertNotIn("resource", query)

    def test_entra_id_begin_redirects_to_microsoft(self):
        response = entra_id_begin(self.build_request())

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            "https://login.microsoftonline.com/tenant-guid/oauth2/v2.0/authorize",
            response["Location"],
        )
