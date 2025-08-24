from django.core.management.base import BaseCommand
from tenants.models import MspCompany
from accounts.models import MSPAuthUser
from django_tenants.utils import tenant_context


class Command(BaseCommand):
    help = 'Create a user for a specific tenant'

    def add_arguments(self, parser):
        parser.add_argument('schema_name', type=str, help='Tenant schema name')
        parser.add_argument('email', type=str, help='User email')
        parser.add_argument('password', type=str, help='User password')
        parser.add_argument('--superuser', action='store_true', help='Create superuser')

    def handle(self, *args, **kwargs):
        schema_name = kwargs['schema_name']
        email = kwargs['email']
        password = kwargs['password']
        is_superuser = kwargs.get('superuser', False)

        try:
            tenant = MspCompany.objects.get(schema_name=schema_name)
            self.stdout.write(f'Found tenant: {tenant.company_name}')

            # Set the tenant context properly
            from django_tenants.utils import schema_context
            with schema_context(tenant.schema_name):
                if is_superuser:
                    user = MSPAuthUser.objects.create_superuser(
                        email=email,
                        password=password
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'Superuser created: {user.email}')
                    )
                else:
                    user = MSPAuthUser.objects.create_user(
                        email=email,
                        password=password
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'User created: {user.email}')
                    )

        except MspCompany.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Tenant with schema "{schema_name}" not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating user: {e}')
            )
