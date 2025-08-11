from django.core.management.base import BaseCommand
from tenants.models import MspCompany


class Command(BaseCommand):
    help = 'Set subscription tier for a company by name'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-name',
            type=str,
            help='Company name to update (partial match supported)',
            required=False
        )
        parser.add_argument(
            '--tier',
            type=str,
            choices=['starter', 'growth', 'innovator'],
            help='Subscription tier to set',
            required=False
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all companies with their current subscription tiers'
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_companies()
            return

        company_name = options['company_name']
        tier = options['tier']

        if not company_name or not tier:
            self.stdout.write(
                self.style.ERROR('Both --company-name and --tier are required')
            )
            return

        # Find companies that match the name (case-insensitive partial match)
        companies = MspCompany.objects.filter(
            company_name__icontains=company_name
        )

        if not companies.exists():
            self.stdout.write(
                self.style.ERROR(f'No companies found matching "{company_name}"')
            )
            return

        if companies.count() > 1:
            self.stdout.write(
                self.style.WARNING(
                    f'Multiple companies found matching "{company_name}":'
                )
            )
            for company in companies:
                self.stdout.write(
                    f'  - {company.company_name} (ID: {company.company_id}, '
                    f'Current Tier: {company.subscription_tier})'
                )
            self.stdout.write(
                self.style.ERROR(
                    'Please use a more specific company name or use the UUID with set_tenant_subscription command'
                )
            )
            return

        # Update the single matching company
        company = companies.first()
        old_tier = company.subscription_tier
        company.subscription_tier = tier
        company.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated company "{company.company_name}" '
                f'from {old_tier} to {tier} tier'
            )
        )

    def list_companies(self):
        """List all companies with their subscription tiers"""
        companies = MspCompany.objects.all().order_by('company_name')
        
        self.stdout.write(self.style.SUCCESS('Current Companies and Subscription Tiers:'))
        self.stdout.write('=' * 60)
        
        for company in companies:
            has_subscription = "Yes" if company.subscription else "No"
            self.stdout.write(
                f'Company: {company.company_name}\n'
                f'  ID: {company.company_id}\n'
                f'  Tier: {company.subscription_tier}\n'
                f'  Has Stripe Subscription: {has_subscription}\n'
                f'  Email: {company.email}\n'
                f'  Domain: {company.schema_name}\n'
                f'  {"-" * 40}'
            ) 