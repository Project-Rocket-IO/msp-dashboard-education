# File: management/commands/generate_fake_data.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.models import TicketList, TechnicianLabor, TechnicianUser, ClientCompany, ProjectList
from faker import Faker
import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Generates fake data for TicketList and TechnicianLabor models'

    def add_arguments(self, parser):
        parser.add_argument('--tickets', type=int, default=200, help='Number of tickets to generate')
        parser.add_argument('--labors', type=int, default=1000, help='Number of labor entries to generate')

    def handle(self, *args, **options):
        fake = Faker()
        num_tickets = options['tickets']
        num_labors = options['labors']

        # Get existing data
        technicians = list(TechnicianUser.objects.all())
        clients = list(ClientCompany.objects.all())
        projects = list(ProjectList.objects.all())

        if not technicians or not clients or not projects:
            self.stdout.write(self.style.ERROR('Ensure you have TechnicianUsers, ClientCompanies, and ProjectLists in the database'))
            return

        # Generate tickets
        tickets = []
        end_date = timezone.now()

        with transaction.atomic():
            for _ in range(num_tickets):
                create_date = fake.date_time_between(start_date='-1y', tzinfo=timezone.get_current_timezone())
                due_date = create_date + timedelta(days=random.randint(1, 30))
                status = random.choices(['New', 'In Progress', 'Closed'], weights=[0.7, 0.1, 0.2])[0]
                
                if status == 'Closed':
                    end_date = due_date + timedelta(days=random.randint(-5, 5))
                else:
                    end_date = None

                ticket = TicketList.objects.create(
                    name=fake.sentence(nb_words=6),
                    description=fake.paragraph(),
                    client=random.choice(clients),
                    end_date=end_date,
                    due_date=due_date,
                    ticket_type=random.choice(['Bug', 'Feature', 'Support']),
                    status=status,
                    priority=random.choice(['Low', 'Medium', 'High']),
                    project=random.choice(projects)
                )
                ticket.assignment.set(random.sample(technicians, k=random.randint(1, 3)))

                ticket.create_date = create_date  # Set the desired date
                ticket.save()

                tickets.append(ticket)

            self.stdout.write(self.style.SUCCESS(f'Successfully created {num_tickets} tickets'))

            # Generate labor entries
            for _ in range(num_labors):
                ticket = random.choice(tickets)
                technician = random.choice(technicians)
                created_at = fake.date_time_between(start_date='-1y', tzinfo=timezone.get_current_timezone())
                
                TechnicianLabor.objects.create(
                    ticket=ticket,
                    minutes=random.randint(15, 480),  # Between 15 minutes and 8 hours
                    is_tracked=random.choice([True, False]),
                    created_by=technician,
                    created_at=created_at,
                    comment=fake.paragraph() if random.random() > 0.5 else None
                )

            self.stdout.write(self.style.SUCCESS(f'Successfully created {num_labors} labor entries'))

        self.stdout.write(self.style.SUCCESS('Fake data generation completed'))