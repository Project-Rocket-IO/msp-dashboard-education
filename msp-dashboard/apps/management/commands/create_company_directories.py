from django.core.management.base import BaseCommand
from django_tenants.utils import tenant_context
from tenants.models import MspCompany
from apps.utils import create_tenant_directories


class Command(BaseCommand):
    help = 'Create directory structure for all existing MspCompanies'

    def handle(self, *args, **options):
        companies = MspCompany.objects.all()
        
        for company in companies:
            try:
                with tenant_context(company):
                    create_tenant_directories()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created directories for company: {company.company_name}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error creating directories for company {company.company_name}: {e}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS('Directory creation process completed!')
        ) 