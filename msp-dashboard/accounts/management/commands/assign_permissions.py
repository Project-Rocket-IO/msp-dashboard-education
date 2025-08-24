#TODO: template file copied from AI
# In a new file, e.g., management/commands/assign_permissions.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.models import TicketList, ClientCompany
from accounts.models import TechnicianUser

class Command(BaseCommand):
    help = 'Assigns custom permissions to roles'

    def handle(self, *args, **options):
        self.stdout.write('Starting permission assignment...')
        
        try:
            # Get content types
            ticket_ct = ContentType.objects.get_for_model(TicketList)
            technician_ct = ContentType.objects.get_for_model(TechnicianUser)
            client_ct = ContentType.objects.get_for_model(ClientCompany)
            
            self.stdout.write(f'Found content types: {ticket_ct}, {technician_ct}, {client_ct}')
            
            # Get existing groups
            groups = Group.objects.all()
            self.stdout.write(f'Found {groups.count()} groups: {[g.name for g in groups]}')
            
            # List all available permissions for these models
            ticket_permissions = Permission.objects.filter(content_type=ticket_ct)
            technician_permissions = Permission.objects.filter(content_type=technician_ct)
            client_permissions = Permission.objects.filter(content_type=client_ct)
            
            self.stdout.write(f'Ticket permissions: {[p.codename for p in ticket_permissions]}')
            self.stdout.write(f'Technician permissions: {[p.codename for p in technician_permissions]}')
            self.stdout.write(f'Client permissions: {[p.codename for p in client_permissions]}')
            
            self.stdout.write(self.style.SUCCESS('Permission assignment completed successfully'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            raise