import random
from locust import HttpUser, task, between
from locustfiles.base import BaseUser

class TicketsUser(BaseUser, HttpUser):

    wait_time = between(1, 5)
    @task(3)
    def browse_ticket_list_page(self):
        self.client.get("/apps/support-tickets/list", name="/apps/support-tickets/list")

    @task(2)
    def browse_tickets_detail_page(self):
        ticket_pk = self.get_random_ticket_pk()
        self.client.get(f"/apps/support-tickets/details/{ticket_pk}", name="/apps/support-tickets/details")

    @task(1)
    def browse_ticket_edit(self):
        ticket_pk = self.get_random_ticket_pk()
        self.client.get(f"/apps/support-tickets/edit/{ticket_pk}", name="/apps/support-tickets/edit")

    @task(2)
    def browse_ticket_time_entry(self):
        ticket_pk = self.get_random_ticket_pk()
        self.client.get(f"/apps/support-tickets/time/{ticket_pk}", name="/apps/support-tickets/time_entry")

    @task(1)
    def browse_ticket_comments(self):
        ticket_pk = self.get_random_ticket_pk()
        self.client.get(f"/apps/support-tickets/comments/{ticket_pk}", name="/apps/support-tickets/comments")

    @task(1)
    def browse_ticket_replies(self):
        ticket_pk = self.get_random_ticket_pk()
        self.client.get(f"/apps/support-tickets/replies/{ticket_pk}", name="/apps/support-tickets/replies")

    def get_random_ticket_pk(self):
        return random.randint(5, 10)
    
