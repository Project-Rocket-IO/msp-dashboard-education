from django.core.management.base import BaseCommand
from tenants.models import MspCompany


class Command(BaseCommand):
    help = 'Set subscription tier for a tenant/company'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=str,
            help='Tenant ID (company_id) to update',
            required=True
        )
        parser.add_argument(
            '--tier',
            type=str,
            choices=['starter', 'growth', 'innovator'],
            help='Subscription tier to set',
            required=True
        )
        parser.add_argument(
            '--list-tenants',
            action='store_true',
            help='List all tenants with their current subscription tiers'
        )

    def handle(self, *args, **options):
        if options['list_tenants']:
            self.list_tenants()
            return

        tenant_id = options['tenant_id']
        tier = options['tier']

        try:
            # Try to find tenant by company_id (UUID)
            tenant = MspCompany.objects.get(company_id=tenant_id)
        except MspCompany.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Tenant with ID {tenant_id} not found')
            )
            return

        # Update the subscription tier
        old_tier = tenant.subscription_tier
        tenant.subscription_tier = tier
        tenant.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated tenant "{tenant.company_name}" '
                f'from {old_tier} to {tier} tier'
            )
        )

    def list_tenants(self):
        """List all tenants with their subscription tiers"""
        tenants = MspCompany.objects.all().order_by('company_name')
        
        self.stdout.write(self.style.SUCCESS('Current Tenants and Subscription Tiers:'))
        self.stdout.write('=' * 60)
        
        for tenant in tenants:
            has_subscription = "Yes" if tenant.subscription else "No"
            self.stdout.write(
                f'Company: {tenant.company_name}\n'
                f'  ID: {tenant.company_id}\n'
                f'  Tier: {tenant.subscription_tier}\n'
                f'  Has Stripe Subscription: {has_subscription}\n'
                f'  Email: {tenant.email}\n'
                f'  Domain: {tenant.schema_name}\n'
                f'  {"-" * 40}'
            ) 