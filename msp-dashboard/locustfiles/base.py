class BaseUser(object):

    def on_start(self):
        self.login()

    def login(self):
        response = self.client.get("/account/login/")
        self.csrftoken = response.cookies.get('csrftoken')

        self.client.post(
            "/account/login/",
            {
                "login": "admin",
                "password": "1234",
                "csrfmiddlewaretoken": self.csrftoken
            },
            headers={"X-CSRFToken": self.csrftoken},
            cookies={"csrftoken": self.csrftoken},
            name="POST /account/login",
        )
