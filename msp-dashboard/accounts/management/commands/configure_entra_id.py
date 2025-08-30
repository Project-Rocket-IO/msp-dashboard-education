from django.core.management.base import BaseCommand
from tenants.models import MspCompany
from django_tenants.utils import tenant_context


class Command(BaseCommand):
    help = 'Configure Entra ID (Azure AD) settings for a tenant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            required=True,
            help='Tenant schema name (e.g., assumption)'
        )
        parser.add_argument(
            '--enable',
            action='store_true',
            help='Enable Entra ID authentication for this tenant'
        )
        parser.add_argument(
            '--tenant-id',
            type=str,
            help='Microsoft Entra ID Tenant ID (Directory ID)'
        )
        parser.add_argument(
            '--client-id',
            type=str,
            help='Microsoft Entra ID Application (Client) ID'
        )
        parser.add_argument(
            '--client-secret',
            type=str,
            help='Microsoft Entra ID Application Client Secret'
        )
        parser.add_argument(
            '--show',
            action='store_true',
            help='Show current Entra ID configuration for the tenant'
        )

    def handle(self, *args, **options):
        tenant_schema = options['tenant']
        
        try:
            # Get tenant from public schema
            tenant = MspCompany.objects.get(schema_name=tenant_schema)
            self.stdout.write(f'Found tenant: {tenant.company_name} ({tenant.schema_name})')
            
            if options['show']:
                self.show_config(tenant)
                return
            
            # Update configuration
            if options['enable'] is not None:
                tenant.enable_entra_id_auth = options['enable']
                self.stdout.write(f'Set enable_entra_id_auth to: {options["enable"]}')
            
            if options['tenant_id']:
                tenant.entra_id_tenant_id = options['tenant_id']
                self.stdout.write(f'Set entra_id_tenant_id to: {options["tenant_id"]}')
            
            if options['client_id']:
                tenant.entra_id_client_id = options['client_id']
                self.stdout.write(f'Set entra_id_client_id to: {options["client_id"]}')
            
            if options['client_secret']:
                tenant.entra_id_client_secret = options['client_secret']
                self.stdout.write(f'Set entra_id_client_secret to: [HIDDEN]')
            
            tenant.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully updated Entra ID configuration for {tenant.company_name}'))
            
            # Show updated configuration
            self.show_config(tenant)
            
        except MspCompany.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Tenant with schema "{tenant_schema}" not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def show_config(self, tenant):
        """Show current Entra ID configuration"""
        self.stdout.write('\n=== Current Entra ID Configuration ===')
        self.stdout.write(f'Enable Entra ID Auth: {tenant.enable_entra_id_auth}')
        self.stdout.write(f'Tenant ID: {tenant.entra_id_tenant_id or "Not configured"}')
        self.stdout.write(f'Client ID: {tenant.entra_id_client_id or "Not configured"}')
        self.stdout.write(f'Client Secret: {"Configured" if tenant.entra_id_client_secret else "Not configured"}')
        
        # Check if configuration is complete
        if tenant.enable_entra_id_auth:
            if all([tenant.entra_id_tenant_id, tenant.entra_id_client_id, tenant.entra_id_client_secret]):
                self.stdout.write(self.style.SUCCESS('✅ Entra ID configuration is complete and ready to use'))
            else:
                self.stdout.write(self.style.WARNING('⚠️  Entra ID is enabled but configuration is incomplete'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Entra ID authentication is disabled'))

