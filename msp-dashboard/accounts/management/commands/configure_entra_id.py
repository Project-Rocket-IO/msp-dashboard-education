from django.core.management.base import BaseCommand

from tenants.models import MspCompany


class Command(BaseCommand):
    help = "Configure Entra ID (Azure AD) settings for a tenant"

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant",
            type=str,
            required=True,
            help="Tenant schema name (e.g., assumption)",
        )
        state_group = parser.add_mutually_exclusive_group()
        state_group.add_argument(
            "--enable",
            action="store_true",
            help="Enable Entra ID authentication for this tenant",
        )
        state_group.add_argument(
            "--disable",
            action="store_true",
            help="Disable Entra ID authentication for this tenant",
        )
        parser.add_argument(
            "--tenant-id",
            type=str,
            help="Microsoft Entra ID Tenant ID (Directory ID)",
        )
        parser.add_argument(
            "--client-id",
            type=str,
            help="Microsoft Entra ID Application (Client) ID",
        )
        parser.add_argument(
            "--client-secret",
            type=str,
            help="Microsoft Entra ID Application Client Secret",
        )
        parser.add_argument(
            "--client-secret-id",
            type=str,
            help="Optional Microsoft Entra ID client secret identifier",
        )
        parser.add_argument(
            "--show",
            action="store_true",
            help="Show current Entra ID configuration for the tenant",
        )

    def handle(self, *args, **options):
        tenant_schema = options["tenant"]

        try:
            tenant = MspCompany.objects.get(schema_name=tenant_schema)
            self.stdout.write(
                f"Found tenant: {tenant.company_name} ({tenant.schema_name})"
            )

            if options["show"]:
                self.show_config(tenant)
                return

            if options["enable"]:
                tenant.enable_entra_id_auth = True
                self.stdout.write("Set enable_entra_id_auth to: True")

            if options["disable"]:
                tenant.enable_entra_id_auth = False
                self.stdout.write("Set enable_entra_id_auth to: False")

            if options["tenant_id"]:
                tenant.entra_id_tenant_id = options["tenant_id"]
                self.stdout.write(
                    f'Set entra_id_tenant_id to: {options["tenant_id"]}'
                )

            if options["client_id"]:
                tenant.entra_id_client_id = options["client_id"]
                self.stdout.write(
                    f'Set entra_id_client_id to: {options["client_id"]}'
                )

            if options["client_secret"]:
                tenant.entra_id_client_secret = options["client_secret"]
                self.stdout.write("Set entra_id_client_secret to: [HIDDEN]")

            if options["client_secret_id"]:
                tenant.entra_id_client_secret_id = options["client_secret_id"]
                self.stdout.write(
                    f'Set entra_id_client_secret_id to: {options["client_secret_id"]}'
                )

            tenant.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated Entra ID configuration for {tenant.company_name}"
                )
            )
            self.show_config(tenant)

        except MspCompany.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Tenant with schema "{tenant_schema}" not found')
            )
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Error: {exc}"))

    def show_config(self, tenant):
        """Show current Entra ID configuration."""
        self.stdout.write("\n=== Current Entra ID Configuration ===")
        self.stdout.write(f"Enable Entra ID Auth: {tenant.enable_entra_id_auth}")
        self.stdout.write(
            f'Tenant ID: {tenant.entra_id_tenant_id or "Not configured"}'
        )
        self.stdout.write(
            f'Client ID: {tenant.entra_id_client_id or "Not configured"}'
        )
        self.stdout.write(
            "Client Secret: "
            + ("Configured" if tenant.entra_id_client_secret else "Not configured")
        )
        self.stdout.write(
            "Client Secret ID: "
            + (tenant.entra_id_client_secret_id or "Not configured")
        )
        self.stdout.write(f"Callback URL: {tenant.get_entra_id_callback_url()}")

        if tenant.enable_entra_id_auth:
            if tenant.is_entra_id_configured:
                self.stdout.write(
                    self.style.SUCCESS(
                        "Entra ID configuration is complete and ready to use"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "Entra ID is enabled but configuration is incomplete"
                    )
                )
        else:
            self.stdout.write(
                self.style.WARNING("Entra ID authentication is disabled")
            )
