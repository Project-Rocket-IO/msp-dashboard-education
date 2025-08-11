from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.contrib import messages
from django.db import connection
from accounts.models import MSPAuthUser
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import update_session_auth_hash, authenticate, login
from django_tenants.utils import schema_context
from allauth.account.views import LoginView
from projectRocket.forms import PasswordSetForm
from tenants.models import MspCompany, Domain
from urllib.parse import urlparse

# LOGIN API

def dual_login_view(request):
    """Authenticate users with both Django Authentication System
    and Django Rest Framework"""
    if request.method == "POST":
        username = request.POST.get("login")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Login user and create session
            login(request, user)
            parsed_url = urlparse(request.build_absolute_uri())
            current_domain = parsed_url.netloc
            user_domain = Domain.objects.get(domain=current_domain)
            company_login = MspCompany.objects.get(company_id=user_domain.tenant_id)
            # Retrieve tenant information
            schema_name = company_login.schema_name
            # Create or get API token, schema-aware
            with schema_context(schema_name):
                token, created = Token.objects.get_or_create(user=user)

            response_data = {"status": "success", "token": token.key}
            return JsonResponse(response_data)
        else:
            return JsonResponse(
                {"status": "error", "message": "Username with the password doesn't exist!"}, status=400
            )

        
    return JsonResponse(
        {"status": "error", "message": "Invalid request method"}, status=405
    )



class CustomLoginView(LoginView):

    def form_invalid(self, form):
        for error in form.errors.values():
            for e in error:
                messages.error(self.request, e)
        return super().form_invalid(form)


class UserLoginAPIView(APIView):

    def post(self, request):
        if not (request.user and request.user.is_authenticated):
            return Response(
                {"error": "User not recognized"}, status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            token, created = Token.objects.get_or_create(user=request.user)
            return Response({"token": f"Token {token.key}"}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )


def profile_settings_password_set(request):
    if request.method == "POST":
        form = PasswordSetForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in even after changing password
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect("dashboards:dashboard_analytics")
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = PasswordSetForm(user=request.user)

    return render(
        request,
        "dashboard/dashboard_analytics.html",
        {"form": form},  # This is needed for error messages and validation
    )



class UserLoginAPIView(APIView):
    def post(self, request):
        """Handle user login and return an authentication token."""
        username = request.data.get("username")
        password = request.data.get("password")

        try:
            user = MSPAuthUser.objects.get(username=username)

            # Verify password
            if not user.check_password(password):
                raise ValueError("Invalid credentials")

            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": f"Token {token.key}"}, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)