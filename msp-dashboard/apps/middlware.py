from django.contrib import messages
from django.contrib.auth.models import Group
from apps.models import ClientCompany, Invoice, TicketList
from django.db.models import Sum
from django.shortcuts import redirect
from django_otp.plugins.otp_email.models import EmailDevice
from django_tenants.utils import tenant_context
import time


class ClientThresholdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Remove duplicate warnings because of redirects and multiple requests
        if (
            "invoices/callback" in request.path
            or "invoices/connect/" in request.path
            or "invoices/connected/" in request.path
            or "support-tickets/time" in request.path
        ):
            return self.get_response(request)

        if "/images/" in request.path:
            return self.get_response(request)

        if "/static/" in request.path:
            return self.get_response(request)

        if "/media/" in request.path:
            return self.get_response(request)

        if "/favicon.ico" in request.path:
            return self.get_response(request)

        # Only process for authenticated users
        if request.user.is_authenticated:
            # Check if user is in admin group
            admin_group = Group.objects.get(name="Administrator")
            if admin_group in request.user.groups.all():
                # Get all client companies
                client_companies = ClientCompany.objects.all()

                for client in client_companies:
                    if client.threshold:  # Only check if threshold is set
                        # Get all invoices for this client
                        invoice = Invoice.objects.filter(client=client).first()
                        if invoice:
                            total_paid = invoice.amount_paid
                        else:
                            total_paid = 0
                        # If client never paid
                        if total_paid == 0:
                            messages.warning(
                                request,
                                f"Make sure to ask {client.name} to pay, prepaid amount is $0",
                                extra_tags="client_threshold_warning",
                            )
                            continue
                        # Get all tickets for this client
                        tickets = TicketList.objects.filter(client=client)
                        # Calculate total labor cost (hours * rate)
                        total_labor_cost = sum(
                            (
                                int(
                                    ticket.technician_labor.all().aggregate(
                                        Sum("minutes")
                                    )["minutes__sum"]
                                    / 60
                                )
                            )
                            * 25
                            for ticket in tickets
                        )
                        # Calculate remaining amount
                        remaining_amount = total_paid - total_labor_cost
                        if remaining_amount < 0:
                            messages.error(
                                request,
                                f"{client.name} has negative prepaid amount. Amount of work worth ${total_labor_cost:.2f} has been done but only ${total_paid:.2f} has been paid.",
                                extra_tags="client_threshold_warning_danger",
                            )
                            continue
                        # Check if remaining amount is less than threshold
                        if remaining_amount < client.threshold:
                            messages.warning(
                                request,
                                f"{client.name} has ${remaining_amount:.2f} remaining, which is below their threshold of ${client.threshold}.",
                                extra_tags="client_threshold_warning",
                            )

        response = self.get_response(request)
        return response


class EnforceTwoFactorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("[EnforceTwoFactorMiddleware] Called for path:", request.path)
        
        # Skip 2FA check for static files, media, and 2FA-related URLs
        if any(
            path in request.path
            for path in [
                "/static/",
                "/media/",
                "/favicon.ico",
                "/two_factor/",
                "/accounts/",
                "/admin/",
                "/logout/", # Yes I should be able to logout without 2fa
                "/setup_complete/",  # Add setup completion URL
                "/complete/",  # Add any completion URLs
                "/account/two_factor/",  # Add account 2FA URLs
                "/login/",  # Allow login without 2FA
                "/signup/",  # Allow signup without 2FA
                "/password/",  # Allow password reset without 2FA
            ]
        ):
            return self.get_response(request)

        # Only check authenticated users
        if request.user.is_authenticated:
            try:
                # Get current tenant
                tenant = getattr(request, 'tenant', None)
                
                # Check if user has 2FA enabled in the current tenant context
                device = None
                if tenant:
                    with tenant_context(tenant):
                        device = EmailDevice.objects.filter(user=request.user).first()
                else:
                    # Fallback to current context
                    device = EmailDevice.objects.filter(user=request.user).first()
                
                # If no device is found, user doesn't have 2FA enabled
                if not device:
                    # Don't show the message if we're already on the setup page or related pages
                    if not any(
                        path in request.path
                        for path in [
                            "setup",
                            "complete",
                            "profile",
                            "backup",
                            "phone",
                            "two_factor",
                            "account/two_factor",
                            "login",
                            "signup",
                            "password",
                        ]
                    ):
                        # Only show message if user is NOT coming from a 2FA-related page
                        # This means they're trying to access protected pages directly
                        
                        http_referer = request.META.get("HTTP_REFERER", request.path)
                        if not any(
                            path in http_referer
                            for path in [
                                "login",
                                "logout",
                                "register",
                                "signup",
                                "password_reset",
                                "password_reset/done",
                                "reset",
                                "reset/done",
                                "two_factor",
                                "account/two_factor",
                            ]
                        ):
                            messages.error(
                                request,
                                "You must enable two-factor authentication to access this application.",
                                extra_tags="2fa_required",
                            )
                        return redirect("apps:two_factor_setup")
            except ImportError:
                print(
                    "[EnforceTwoFactorMiddleware] ImportError: django-two-factor-auth not available. Skipping 2FA check."
                )
                pass
            except Exception as e:
                print(f"[EnforceTwoFactorMiddleware] Exception: {e}")
                pass
        else:
            print(
                f"[EnforceTwoFactorMiddleware] User is not authenticated. Skipping 2FA check."
            )
        response = self.get_response(request)
        print("[EnforceTwoFactorMiddleware] Response returned.")
        return response
