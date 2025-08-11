from django.core.management.base import BaseCommand
from apps.models import TicketList, ProjectList


class Command(BaseCommand):
    help = 'Fix inconsistencies between ticket-project ForeignKey and ManyToMany relationships'

    def handle(self, *args, **options):
        self.stdout.write("Starting to fix ticket-project relationships...")
        
        # Get all tickets
        tickets = TicketList.objects.all()
        fixed_count = 0
        
        for ticket in tickets:
            # Check if ticket has a ForeignKey project
            fk_project = ticket.project
            
            # Check if ticket is in any project's ManyToMany relationship
            mm_projects = ProjectList.objects.filter(tickets=ticket)
            
            if fk_project and not mm_projects.exists():
                # Ticket has ForeignKey but not in ManyToMany - add to ManyToMany
                fk_project.tickets.add(ticket)
                self.stdout.write(f"Added ticket {ticket.name} to project {fk_project.name} (ManyToMany)")
                fixed_count += 1
                
            elif not fk_project and mm_projects.exists():
                # Ticket is in ManyToMany but no ForeignKey - set ForeignKey
                mm_project = mm_projects.first()
                ticket.project = mm_project
                ticket.save()
                self.stdout.write(f"Set ForeignKey for ticket {ticket.name} to project {mm_project.name}")
                fixed_count += 1
                
            elif fk_project and mm_projects.exists():
                # Both relationships exist - check if they match
                mm_project = mm_projects.first()
                if fk_project != mm_project:
                    # Mismatch - fix by using the ManyToMany project
                    ticket.project = mm_project
                    ticket.save()
                    self.stdout.write(f"Fixed mismatch for ticket {ticket.name}: ForeignKey now points to {mm_project.name}")
                    fixed_count += 1
                    
            elif not fk_project and not mm_projects.exists():
                # No relationships - this is fine (ticket not assigned to any project)
                pass
                
        self.stdout.write(
            self.style.SUCCESS(f'Successfully fixed {fixed_count} ticket-project relationships!')
        ) 