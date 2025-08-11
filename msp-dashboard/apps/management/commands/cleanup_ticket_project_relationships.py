from django.core.management.base import BaseCommand
from apps.models import TicketList, ProjectList


class Command(BaseCommand):
    help = 'Clean up inconsistent ticket-project relationships'

    def handle(self, *args, **options):
        self.stdout.write("Starting to clean up ticket-project relationships...")
        
        cleaned_count = 0
        
        # Get all projects
        projects = ProjectList.objects.all()
        
        for project in projects:
            # Get all tickets in the ManyToMany relationship
            mm_tickets = project.tickets.all()
            
            for ticket in mm_tickets:
                # Check if the ticket's ForeignKey points to this project
                if ticket.project != project:
                    # Remove from ManyToMany if ForeignKey doesn't match
                    project.tickets.remove(ticket)
                    # Also clear the ForeignKey if it was pointing to this project
                    if ticket.project == project:
                        ticket.project = None
                        ticket.save()
                    self.stdout.write(f"Removed ticket '{ticket.name}' from project '{project.name}' (ForeignKey mismatch)")
                    cleaned_count += 1
        
        # Also check for tickets with ForeignKey but not in ManyToMany
        tickets_with_fk = TicketList.objects.filter(project__isnull=False)
        
        for ticket in tickets_with_fk:
            project = ticket.project
            if not project.tickets.filter(pk=ticket.pk).exists():
                # Add to ManyToMany if missing
                project.tickets.add(ticket)
                self.stdout.write(f"Added ticket '{ticket.name}' to project '{project.name}' (ManyToMany missing)")
                cleaned_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleaned up {cleaned_count} ticket-project relationships!')
        ) 