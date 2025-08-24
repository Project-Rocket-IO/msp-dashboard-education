from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from apps.forms import (
    WebviewIntegrationsAddForm,
)
from apps.models import WebviewIntegrations, ClientCompany, ProjectList, TicketList, ClientCompanyFiles, ClientLocations, ClientTeamMembers
from .utils import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from rbac.utils import paginate_queryset
from rbac.decorators import has_permission
from apps.models import TechnicianUser
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
        print("DEBUG: Form submitted to pages_create_account")
        
        # ? We're basically converting a dictionary of lists
        # ? to  list of dictionaries, in the following code
        form_data_sets = get_form_data_sets(request.POST)  # properly structure data
        result = process_form_data_sets(form_data_sets, request.user)
        
        if isinstance(result, tuple) and result[0] == "billing_required":
            # Billing is required - redirect to Stripe checkout
            billing_sessions = result[1]
            if len(billing_sessions) == 1:
                # Single user - redirect to Stripe
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
@has_permission("accounts.view_technicianuser")
def pages_profile_settings(request):
    """Update User Profile Settings Page"""
    user = request.user
    
    # Check if user is superuser or administrator
    if not (user.is_superuser or user.groups.filter(name__in=['Administrator', 'Super User']).exists()):
        messages.error(request, "Access denied. Only administrators and superusers can access this page.")
        return redirect("pages:pages.profile")
    
    context = get_context_data(user)
    
    # Add DEBUG setting to context for JavaScript
    from django.conf import settings
    context['settings'] = settings
    
    # Add groups to context for dynamic role options
    from django.contrib.auth.models import Group
    available_groups = Group.objects.all().order_by('id')
    context['available_groups'] = available_groups
    


    # Check for payment success parameters
    session_id = request.GET.get('session_id')
    user_created = request.GET.get('user_created')
    
    if session_id and user_created == 'true':
        # Payment was successful, try to create user manually
        try:
            import stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Retrieve the session to get metadata
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid' and session.metadata.get('user_email'):
                # Payment was successful, create the user
                from pages.utils import create_user_without_billing
                
                # Prepare form data from metadata
                form_data = (
                    session.metadata.get('first_name', ''),
                    session.metadata.get('last_name', ''),
                    session.metadata.get('user_email', ''),
                    session.metadata.get('client_id', ''),
                    int(session.metadata.get('role_id', '')),
                    session.metadata.get('phone', ''),
                    session.metadata.get('title', ''),
                    session.metadata.get('password', '')
                )
                
                success, error = create_user_without_billing(form_data)
                if success:
                    messages.success(request, f"Payment successful! User {session.metadata.get('user_email')} has been created.")
                else:
                    messages.error(request, f"Payment successful but user creation failed: {error}")
            else:
                messages.warning(request, "Payment completed but user data not found in session.")
                
        except Exception as e:
            messages.error(request, f"Error processing payment completion: {str(e)}")

    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "edit_user":
            # Handle user editing
            user_id = request.POST.get("user_id")
            try:
                User = get_user_model()
                target_user = User.objects.get(user_id=user_id)
                
                # Update user fields
                target_user.first_name = request.POST.get("first_name", "")
                target_user.last_name = request.POST.get("last_name", "")
                target_user.email = request.POST.get("email", "")
                target_user.phone = request.POST.get("phone", "")
                target_user.title = request.POST.get("title", "")
                
                # Update role (group)
                role_id = request.POST.get("role")
                if role_id:
                    try:
                        new_group = Group.objects.get(id=role_id)
                        target_user.groups.clear()
                        target_user.groups.add(new_group)
                    except Group.DoesNotExist:
                        messages.error(request, f"Role with ID {role_id} not found.")
                        return redirect("pages:pages.profile_settings")
                
                target_user.save()
                messages.success(request, f"User {target_user.username} updated successfully.")
                
            except User.DoesNotExist:
                messages.error(request, f"User with ID {user_id} not found.")
            except Exception as e:
                messages.error(request, f"Error updating user: {str(e)}")
                
        elif action == "delete_user":
            # Handle user deletion
            user_id = request.POST.get("user_id")
            try:
                User = get_user_model()
                target_user = User.objects.get(user_id=user_id)
                username = target_user.username
                
                # Prevent self-deletion
                if target_user == user:
                    messages.error(request, "You cannot delete your own account.")
                    return redirect("pages:pages.profile_settings")
                
                # Get the TechnicianUser instance if it exists
                technician_user = None
                try:
                    from accounts.models import TechnicianUser
                    technician_user = TechnicianUser.objects.get(auth_user=target_user)
                except TechnicianUser.DoesNotExist:
                    pass
                
                # Handle tickets and projects cleanup
                from apps.models import TicketList, ProjectList
                
                # Handle tickets
                if technician_user:
                    # Get all tickets assigned to this technician
                    assigned_tickets = TicketList.objects.filter(assignment=technician_user)
                    
                    for ticket in assigned_tickets:
                        # If this is the only technician assigned, set assignment to null
                        if ticket.assignment.count() == 1:
                            ticket.assignment.clear()
                        else:
                            # Remove this technician from the assignment
                            ticket.assignment.remove(technician_user)
                
                # Handle projects
                if technician_user:
                    # Get all projects assigned to this technician
                    assigned_projects = ProjectList.objects.filter(assignment=technician_user)
                    
                    for project in assigned_projects:
                        # If this is the only technician assigned, set assignment to null
                        if project.assignment.count() == 1:
                            project.assignment.clear()
                        else:
                            # Remove this technician from the assignment
                            project.assignment.remove(technician_user)
                
                # Delete the user
                from django.db import connection
                
                try:
                    print(f"DEBUG: Starting deletion process for user {username}")
                    print(f"DEBUG: User ID: {target_user.user_id}")
                    print(f"DEBUG: User email: {target_user.email}")
                    
                    with connection.cursor() as cursor:
                        # Check if user exists in MSPAuthUser table
                        cursor.execute("SELECT COUNT(*) FROM accounts_mspauthuser WHERE user_id = %s", [target_user.user_id])
                        user_count = cursor.fetchone()[0]
                        print(f"DEBUG: User count in MSPAuthUser table: {user_count}")
                        # Clear user groups relationship
                        cursor.execute(
                            "DELETE FROM accounts_mspauthuser_groups WHERE mspauthuser_id = %s",
                            [target_user.user_id]
                        )
                        
                        # Clear user permissions relationship
                        cursor.execute(
                            "DELETE FROM accounts_mspauthuser_user_permissions WHERE mspauthuser_id = %s",
                            [target_user.user_id]
                        )
                        
                        # Clear calendar events
                        cursor.execute(
                            "DELETE FROM calendar_event_calendarevents WHERE creator_id = %s",
                            [target_user.user_id]
                        )
                        
                        # Clear calendar event guests
                        cursor.execute(
                            "DELETE FROM calendar_event_calendarevents_guests WHERE mspauthuser_id = %s",
                            [target_user.user_id]
                        )
                        
                        # Clear comments and other user-related data
                        cursor.execute(
                            "DELETE FROM apps_ticketcomment WHERE user_id = %s",
                            [target_user.user_id]
                        )
                        cursor.execute(
                            "DELETE FROM apps_ticketcommentreplies WHERE user_id = %s",
                            [target_user.user_id]
                        )
                        cursor.execute(
                            "DELETE FROM apps_projectcomment WHERE user_id = %s",
                            [target_user.user_id]
                        )
                        cursor.execute(
                            "DELETE FROM apps_projectcommentreplies WHERE user_id = %s",
                            [target_user.user_id]
                        )
                        cursor.execute(
                            "DELETE FROM apps_webviewintegrations WHERE user_id = %s",
                            [target_user.user_id]
                        )
                        
                        # Delete TechnicianUser first if it exists
                        if technician_user:
                            cursor.execute(
                                "DELETE FROM accounts_technicianuser WHERE auth_user_id = %s",
                                [target_user.user_id]
                            )
                        
                        # Delete MSPAuthUser
                        print(f"DEBUG: Deleting MSPAuthUser with user_id: {target_user.user_id}")
                        cursor.execute(
                            "DELETE FROM accounts_mspauthuser WHERE user_id = %s",
                            [target_user.user_id]
                        )
                        print(f"DEBUG: MSPAuthUser deletion completed")
                    
                    messages.success(request, f"User {username} deleted successfully. All associated tickets and projects have been updated.")
                    
                except Exception as sql_error:
                    raise sql_error
                
            except User.DoesNotExist:
                messages.error(request, f"User with ID {user_id} not found.")
            except Exception as e:
                messages.error(request, f"Error deleting user: {str(e)}")
        else:
            # Handle regular profile update
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


def pages_profile_with_pk(request, pk):
    """Profile view that accepts a client pk and displays client data using the profile template"""
    company = get_object_or_404(ClientCompany, pk=pk)

    # Get client data similar to the client details view
    projects = ProjectList.objects.filter(client_id=company)
    tickets = TicketList.objects.filter(client_id=company)
    client_files = ClientCompanyFiles.objects.filter(client_id=pk)
    client_locations = ClientLocations.objects.filter(client_id=pk)
    client_members = ClientTeamMembers.objects.filter(client_id=pk)
    clients = ClientCompany.objects.all().order_by("-name")
    technicians = TechnicianUser.objects.all()
    all_tickets = TicketList.objects.all()
    all_projects = ProjectList.objects.all()

    # Pagination for tickets
    client_tickets_page_number = request.GET.get("client_ticket_page", 1)
    tickets, ticketsPaginator = paginate_queryset(
        tickets, client_tickets_page_number, per_page=8
    )

    query_params_pagination_type = request.GET.get(
        "client_ticket_page"
    ) or request.GET.get("client_project_page")

    active_tab = "overview"
    if query_params_pagination_type:
        if "client_ticket_page" in request.GET:
            active_tab = "tickets"
        elif "client_project_page" in request.GET:
            active_tab = "projects"

    context = {
        "technicians": technicians,
        "tickets": tickets,
        "ticketPaginator": ticketsPaginator,
        "all_tickets": all_tickets,
        "clients": clients,
        "projects": projects,
        "all_projects": all_projects,
        "company": company,
        "client_files": client_files,
        "client_locations": client_locations,
        "client_members": client_members,
        "active_tab": active_tab,
        # Add user context for the profile template
        "user": company,  # Use company as user for the profile template
    }

    return render(request, "pages/pages-profile.html", context=context)
