from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages


class PasswordUpdateWarningMiddleware(MiddlewareMixin):
    def process_response(self, request, response):

        # Remove duplicate warnings because of redirects and multiple requests
        if request.path.endswith("invoices/connect/"):
            return self.get_response(request)

        if "/images/" in request.path:
            return self.get_response(request)

        if "/static/" in request.path:
            return self.get_response(request)

        if "/favicon.ico" in request.path:
            return self.get_response(request)

        # Skip password warning on login, 2FA, and authentication pages
        if any(
            path in request.path
            for path in [
                "/login",
                "/two_factor/",
                "/accounts/",
                "/admin/",
                "/logout/",
                "/signup",
                "/register",
                "/password/",
                "/reset/",
            ]
        ):
            return response

        messages.get_messages(request)
        if request.user.is_authenticated and request.user.password_needs_change:
            messages.warning(
                request,
                "Please update your password from the Settings for security reasons!",
                extra_tags="update_password_warning",
            )
        return response
