from locust import HttpUser, task
from locustfiles.base import BaseUser

class LoginUser(BaseUser, HttpUser):

    @task
    def submit_form(self):
        
        self.client.post(
            "/account/login/",
            {
                "login": "admin",
                "password": "1234",
                "csrfmiddlewaretoken": self.csrftoken,  # Add CSRF token to the form data
            },
            cookies={"csrftoken": self.csrftoken},
            headers={
                "X-CSRFToken": self.csrftoken
            },  # Set CSRF token in the headers if required
            name="POST /account/login",
        )

    @task
    def home(self):
        self.client.get("/", name="/")
