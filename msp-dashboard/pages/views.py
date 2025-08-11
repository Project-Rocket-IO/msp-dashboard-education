from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from apps.forms import (
    WebviewIntegrationsAddForm,
)
from apps.models import WebviewIntegrations, ClientCompany
from .utils import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
# Create your views here.


class PagesView(TemplateView):
    pass


# Authenticatin
authentication_signin_basic = PagesView.as_view(
    template_name="pages/authentication/auth-signin-basic.html"
)
authentication_signin_cover = PagesView.as_view(
    template_name="pages/authentication/auth-signin-cover.html"
)
authentication_signup_basic = PagesView.as_view(
    template_name="pages/authentication/auth-signup-basic.html"
)
authentication_signup_cover = PagesView.as_view(
    template_name="pages/authentication/auth-signup-cover.html"
)
authentication_pass_reset_basic = PagesView.as_view(
    template_name="pages/authentication/auth-pass-reset-basic.html"
)
authentication_pass_reset_cover = PagesView.as_view(
    template_name="pages/authentication/auth-pass-reset-cover.html"
)
authentication_lockscreen_basic = PagesView.as_view(
    template_name="pages/authentication/auth-lockscreen-basic.html"
)
authentication_lockscreen_cover = PagesView.as_view(
    template_name="pages/authentication/auth-lockscreen-cover.html"
)
authentication_logout_basic = PagesView.as_view(
    template_name="pages/authentication/auth-logout-basic.html"
)
authentication_logout_cover = PagesView.as_view(
    template_name="pages/authentication/auth-logout-cover.html"
)
authentication_success_msg_basic = PagesView.as_view(
    template_name="pages/authentication/auth-success-msg-basic.html"
)
authentication_success_msg_cover = PagesView.as_view(
    template_name="pages/authentication/auth-success-msg-cover.html"
)
authentication_twostep_basic = PagesView.as_view(
    template_name="pages/authentication/auth-twostep-basic.html"
)
authentication_twostep_cover = PagesView.as_view(
    template_name="pages/authentication/auth-twostep-cover.html"
)
authentication_404_basic = PagesView.as_view(
    template_name="pages/authentication/auth-404-basic.html"
)
authentication_404_cover = PagesView.as_view(
    template_name="pages/authentication/auth-404-cover.html"
)
authentication_404_alt = PagesView.as_view(
    template_name="pages/authentication/auth-404-alt.html"
)
authentication_500 = PagesView.as_view(
    template_name="pages/authentication/auth-500.html"
)
authentication_pass_change_basic = PagesView.as_view(
    template_name="pages/authentication/auth-pass-change-basic.html"
)
authentication_pass_change_cover = PagesView.as_view(
    template_name="pages/authentication/auth-pass-change-cover.html"
)
authentication_offline = PagesView.as_view(
    template_name="pages/authentication/auth-offline.html"
)

# Pages
pages_starter = PagesView.as_view(template_name="pages/pages-starter.html")
pages_profile = PagesView.as_view(template_name="pages/pages-profile.html")
pages_profile_settings = PagesView.as_view(
    template_name="pages/pages-profile-settings.html"
)
pages_webview_delete_view = PagesView.as_view(
    template_name="pages/pages-profile-settings.html"
)
pages_team = PagesView.as_view(template_name="pages/pages-team.html")
pages_timeline = PagesView.as_view(template_name="pages/pages-timeline.html")
pages_help_center = PagesView.as_view(template_name="pages/pages-help-center.html")
pages_pricing = PagesView.as_view(template_name="pages/pages-pricing.html")
pages_gallery = PagesView.as_view(template_name="pages/pages-gallery.html")
pages_maintenance = PagesView.as_view(template_name="pages/pages-maintenance.html")
pages_coming_soon = PagesView.as_view(template_name="pages/pages-coming-soon.html")
pages_sitemap = PagesView.as_view(template_name="pages/pages-sitemap.html")
pages_search_results = PagesView.as_view(
    template_name="pages/pages-search-results.html"
)
pages_privacy_policy = PagesView.as_view(
    template_name="pages/pages-privacy-policy.html"
)
pages_terms_conditions = PagesView.as_view(
    template_name="pages/pages-term-conditions.html"
)

pages_landing = PagesView.as_view(template_name="pages/pages-landing.html")
pages_nft_landing = PagesView.as_view(template_name="pages/pages-nft-landing.html")
pages_job_landing = PagesView.as_view(template_name="pages/pages-job-landing.html")


# Functions
@login_required
def pages_webview_create_view(request):
    user = request.user
    context = {"user": user}
    if user.is_superuser:
        clients = ClientCompany.objects.filter(main_tech__isnull=True)
        context["clients"] = clients

    webviews = WebviewIntegrations.objects.filter(user=user)
    context["webviews"] = webviews

    if request.method == "POST":
        form = WebviewIntegrationsAddForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = user
            obj.save()
            messages.success(request, "App Integration inserted successfully!")
        else:
            print(form.errors)
            messages.error(request, "Something went wrong!")
    return redirect("pages:pages.profile_settings")


def pages_webview_delete_view(request, pk):
    webview = WebviewIntegrations.objects.get(pk=pk)
    webview.delete()
    messages.success(request, "Webview deleted successfully!")
    return redirect("pages:pages.profile_settings")


@login_required
def pages_create_account(request):
    """Create a User Profile Settings Page using Admin"""
    if request.method == "POST":

        # ? We're basically converting a dictionary of lists
        # ? to  list of dictionaries, in the following code
        form_data_sets = get_form_data_sets(request.POST)  # properly structure data
        result = process_form_data_sets(form_data_sets, request.user)
        
        if isinstance(result, tuple) and result[0] == "billing_required":
            # Billing is required - redirect to Stripe checkout
            billing_sessions = result[1]
            if len(billing_sessions) == 1:
                # Single user - redirect directly to Stripe
                session_data = billing_sessions[0]
                return redirect(session_data["checkout_url"])
            else:
                # Multiple users - we'll need to handle this differently
                # For now, redirect to the first session
                session_data = billing_sessions[0]
                return redirect(session_data["checkout_url"])
        else:
            # Normal processing
            unsuccessful_creations, error_message = result
            
            if unsuccessful_creations == 0:
                messages.success(request, "Successfully Created User Profile")
            else:
                messages.error(
                    request,
                    f"Error creating {unsuccessful_creations} accounts.  {error_message}",
                )

    return redirect("pages:pages.profile_settings")


@login_required
def pages_profile_settings(request):
    """Update User Profile Settings Page"""
    user = request.user
    context = get_context_data(user)

    if request.method == "POST":
        form = process_profile_update_form(request, user)
        if not form.is_valid():
            context["form"] = form
            return redirect("pages:pages.profile_settings")

    return render(request, "pages/pages-profile-settings.html", context=context)


@login_required
def change_password_view(request):
    if request.method == "POST":
        # Clear messages, remove warning message as soon the password is changed
        storage = messages.get_messages(request)
        storage.used = True

        current_password = request.POST.get("oldpassword")
        new_password = request.POST.get("password1")
        confirm_password = request.POST.get("password2")

        user = request.user

        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return redirect("pages:pages.profile_settings")

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return redirect("pages:pages.profile_settings")

        if len(new_password) < 8:
            messages.error(request, "New password must be at least 8 characters long.")
            return redirect("pages:pages.profile_settings")

        user.set_password(new_password)
        user.password_needs_change = False
        user.save()
        update_session_auth_hash(
            request, user
        )  # Important to keep the user logged in after password change
        messages.success(request, "Password successfully changed.")

    return redirect("pages:pages.profile_settings")


@login_required
def set_password_view(request):
    if request.method == "POST":
        new_password = request.POST.get("password1")
        confirm_password = request.POST.get("password2")

        user = request.user

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return redirect("pages:pages.profile_settings")

        if len(new_password) < 8:
            messages.error(request, "New password must be at least 8 characters long.")
            return redirect("pages:pages.profile_settings")

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(
            request, user
        )  # Important to keep the user logged in after password change
        messages.success(request, "Password successfully set.")

    return redirect("pages:pages.profile_settings")

#############
# FAQ PAGES #
