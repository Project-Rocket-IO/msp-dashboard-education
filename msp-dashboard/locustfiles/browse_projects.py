import random
from locust import HttpUser, task
from locustfiles.base import BaseUser

class ProjectsUser(BaseUser, HttpUser):

    @task(3)
    def browse_projects_list(self):
        self.client.get("/apps/projects/list", name="/apps/projects/list")

    @task(2)
    def browse_projects_overview(self):
        project_pk = self.get_random_project_pk()
        self.client.get(f"/apps/projects/overview/{project_pk}", name="/apps/projects/overview")

    @task(1)
    def browse_projects_edit(self):
        project_pk = self.get_random_project_pk()
        self.client.get(f"/apps/projects/edit/{project_pk}", name="/apps/projects/edit")

    @task(1)
    def browse_project_comments(self):
        project_pk = self.get_random_project_pk()
        self.client.get(f"/apps/projects/comments/{project_pk}", name="/apps/projects/comments")

    @task(1)
    def browse_project_replies(self):
        project_pk = self.get_random_project_pk()
        self.client.get(f"/apps/projects/replies/{project_pk}", name="/apps/projects/replies")

    @task(1)
    def browse_project_create(self):
        self.client.post("/apps/projects/create", name="/apps/projects/create")

        
    def get_random_project_pk(self):
        return random.randint(1, 5)
    
