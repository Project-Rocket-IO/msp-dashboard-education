from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import transaction
from apps.models import ClientCompany, TechnicianUser, WebviewIntegrations
from accounts.forms import TechnicianUserForm, MSPAuthUserForm
from accounts.models import UserManager, MSPAuthUser
from django.conf import settings
import stripe
import random, string

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

ROLE_CHOICES = (
    (1, "Administrator"),
    (2, "Bookkeeper"),
    (3, "Lead Technician"),
    (4, "Technician"),
    (5, "Sub Contractor"),
    (6, "Sales"),
    (7, "Project Manager"),
    (8, "Scheduler"),
    (9, "Super User"),
)
CLIENT_ROLE = 10

# Stripe pricing for different roles (in cents)
ROLE_PRICING = {
    1: 5000,  # Administrator - $50
    2: 3000,  # Bookkeeper - $30
    3: 4000,  # Lead Technician - $40
    4: 2500,  # Technician - $25
    5: 3500,  # Sub Contractor - $35
    6: 3000,  # Sales - $30
    7: 4500,  # Project Manager - $45
    8: 2500,  # Scheduler - $25
    9: 6000,  # Super User - $60
    10: 0,    # Client - Free
}

# Subscription tier pricing (in cents)
SUBSCRIPTION_TIERS = {
    'starter': {
        'monthly': 3500,  # $35.00 USD per month
        'yearly': 36000,  # $360.00 USD per year
        'name': 'Starter Tier'
    },
    'growth': {
        'monthly': 5500,  # $55.00 USD per month
        'yearly': 56400,  # $564.00 USD per year
        'name': 'Growth Tier'
    },
    'innovator': {
        'monthly': 7500,  # $75.00 USD per month
        'yearly': 76800,  # $768.00 USD per year
        'name': 'Innovator Tier'
    }
}

def get_user_subscription_tier(user):
    """
    Get the current user's subscription tier.
    This always returns the company's subscription tier, not individual user tier.
    
    Args:
        user: The current user
        
    Returns:
        str: The subscription tier ('starter', 'growth', 'innovator')
    """
    # Get the company's subscription tier (tenant-based)
    if hasattr(user, 'tenant') and user.tenant:
        return user.tenant.get_subscription_tier()
    elif hasattr(user, 'auth_user') and hasattr(user.auth_user, 'tenant') and user.auth_user.tenant:
        return user.auth_user.tenant.get_subscription_tier()
    else:
        # Default to starter tier if no tenant found
        return 'starter'


def create_user_billing_session(role_id, user_email, user_name, current_user, form_data=None):
    """
    Create a Stripe checkout session for user creation billing based on company's subscription tier.
    
    Args:
        role_id (int): The role ID of the user being created
        user_email (str): Email of the user being created
        user_name (str): Name of the user being created
        current_user: The user creating the account (to determine company's subscription tier)
        form_data (dict): Complete form data for user creation
        
    Returns:
        dict: Stripe checkout session data or error
    """
    try:
        print(f"DEBUG: create_user_billing_session called with role_id: {role_id}")
        
        # Get the role name from the database group
        from django.contrib.auth.models import Group
        try:
            group = Group.objects.get(id=role_id)
            role_name = group.name
            print(f"DEBUG: Found group: {role_name}")
        except Group.DoesNotExist:
            print(f"DEBUG: Group with ID {role_id} not found")
            return {"success": False, "error": f"Group with ID {role_id} not found"}
        
        # Only require billing for paid roles
        # Student and Faculty/Staff are free
        # Administration, IT Dept, and Super User require billing
        free_roles = ['Student', 'Faculty/Staff']
        if role_name in free_roles:
            return {"success": True, "no_billing": True}
        
        # Get the company's subscription tier (not individual user tier)
        subscription_tier = get_user_subscription_tier(current_user)
        
        # Get the price for this subscription tier (monthly rate)
        tier_pricing = SUBSCRIPTION_TIERS.get(subscription_tier, SUBSCRIPTION_TIERS['starter'])
        price = tier_pricing['monthly']  # Use monthly rate for user creation
        
        # role_name is already set from the group lookup above
        
        # Prepare metadata with all form data
        metadata = {
            'user_email': user_email,
            'user_name': user_name,
            'role_id': str(role_id),
            'role_name': role_name,
            'subscription_tier': subscription_tier,
            'tier_name': tier_pricing['name'],
            'company_tier': subscription_tier,  # Explicitly mark as company tier
        }
        
        # Add form data to metadata if provided
        if form_data:
            metadata.update({
                'first_name': form_data.get('first_name', ''),
                'last_name': form_data.get('last_name', ''),
                'phone': form_data.get('phone', ''),
                'title': form_data.get('title', ''),
                'password': form_data.get('password', ''),
                'client_id': str(form_data.get('client_id', '')),
            })
        
        # Create checkout session
        try:
            checkout_session = stripe.checkout.Session.create(
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'User Creation - {role_name}',
                            'description': f'One-time charge for creating {user_name} as {role_name} ({tier_pricing["name"]} rate)',
                        },
                        'unit_amount': price,
                    },
                    'quantity': 1,
                }],
                payment_method_types=['card'],
                mode='payment',
                success_url='http://localhost:8000/pages/pages/profile-settings?session_id={CHECKOUT_SESSION_ID}&user_created=true',
                cancel_url='http://localhost:8000/pages/pages/profile-settings?cancelled=true',
                metadata=metadata
            )
        except Exception as stripe_error:
            return {"success": False, "error": f"Stripe error: {str(stripe_error)}"}
        
        result = {
            "success": True,
            "session_id": checkout_session.id,
            "checkout_url": checkout_session.url,
            "amount": price / 100,  # Convert cents to dollars
            "role_name": role_name,
            "subscription_tier": subscription_tier,
            "tier_name": tier_pricing['name']
        }
        print(f"DEBUG: Returning billing session result: {result}")
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# #####################################
# User Create Settings Page
def generate_unique_username(base_str):
    """
    Generate a unique username based on a given base string.

    This function takes a base string, typically derived from a user's email or name, and appends a random 4-digit string to it to create a unique username. It checks the database to ensure that the generated username does not already exist and continues generating new usernames until a unique one is found.

    Args:
        base_str (str): The base string to be used for generating the username.

    Returns:
        str: A unique username.
    """
    # Create a base username
    base_username = base_str.lower().replace(" ", "")
    # Combine base username with random digits
    username = f"{base_username}"
    # Ensure the username is unique
    while MSPAuthUser.objects.filter(username=username).exists():
        random_str = "".join(random.choices(string.digits, k=2))
        username = f"{base_username}{random_str}"
    return username


def get_base_user_str(email, first_name, last_name):
    """
    Generate a base string for the username from email, first name, and last name.

    This function creates a base string that will be used to generate a unique username. It prioritizes the email address's local part, followed by the concatenation of the first name and last name. If neither are available, it defaults to "user".

    Args:
        email (str): The email address of the user.
        first_name (str): The first name of the user.
        last_name (str): The last name of the user.

    Returns:
        str: A base string for generating the username.
    """

    if email:
        base_str = email.split("@")[0]
    elif first_name and last_name:
        base_str = f"{first_name}{last_name}"
    else:
        base_str = "user"

    return base_str


def get_form_data_sets(users_data):
    """
    Split the POST request data into multiple sets for form processing.

    This function takes the POST data from a request and splits it into multiple sets of form data, each containing the information for a single user. It ensures that if no choices are provided, an empty list of the same length as the email list is used.

    Args:
        users_data (QueryDict): The POST data from the request.

    Returns:
        zip: A zip object containing tuples of form data for each user.
    """
    print(f"DEBUG: get_form_data_sets called with users_data: {users_data}")
    print(f"DEBUG: first_name: {users_data.getlist('first_name')}")
    print(f"DEBUG: last_name: {users_data.getlist('last_name')}")
    print(f"DEBUG: email: {users_data.getlist('email')}")
    print(f"DEBUG: client_id: {users_data.getlist('client_id')}")
    print(f"DEBUG: role: {users_data.getlist('role')}")
    print(f"DEBUG: phone: {users_data.getlist('phone')}")
    print(f"DEBUG: title: {users_data.getlist('title')}")
    print(f"DEBUG: password: {users_data.getlist('password')}")

    return zip(
        users_data.getlist("first_name"),
        users_data.getlist("last_name"),
        users_data.getlist("email"),
        users_data.getlist("client_id")
        or ["" for _ in range(len(users_data.getlist("email")))],
        users_data.getlist("role"),
        users_data.getlist("phone"),
        users_data.getlist("title"),
        users_data.getlist("password"),
    )


def create_user(form_data: list, current_user=None):
    """
    Create a user from the provided form data list.

    This function takes a tuple of form data, validates it using the `TechnicianUserForm`, and creates a new user if the data is valid. It generates a unique username, hashes the password, and saves the user. If the user's role is 'Client', it assigns the user as the main technician for the specified client.

    Args:
        form_data_list (tuple): A tuple containing the form data for a user.
        current_user: The user creating the account (to determine company's subscription tier)

    Returns:
        tuple: A tuple containing a boolean indicating success or failure, and an error message if any.
    """
    (first_name, last_name, email, client_id, role, phone, title, password) = form_data
    role_id = int(role)
    
    print(f"DEBUG: create_user - role_id: {role_id}")
    
    # Get the group name from the role ID to determine billing requirements
    from django.contrib.auth.models import Group
    try:
        group = Group.objects.get(id=role_id)
        group_name = group.name
        print(f"DEBUG: create_user - group_name: {group_name}")
    except Group.DoesNotExist:
        return False, f"Group with ID {role_id} not found"
    
    # Check if billing is required based on group name
    # Student and Faculty/Staff are free, others require billing
    free_roles = ['Student', 'Faculty/Staff']
    
    if group_name in free_roles:
        # No billing required, create user directly
        print(f"DEBUG: {group_name} is a free role, creating user without billing")
        return create_user_without_billing(form_data)
    else:
        # Billing required for paid roles
        print(f"DEBUG: {group_name} requires billing")
        user_name = f"{first_name} {last_name}".strip()
        
        # Prepare form data dict for metadata
        form_data_dict = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'client_id': client_id,
            'role': role,
            'phone': phone,
            'title': title,
            'password': password,
        }
        
        billing_result = create_user_billing_session(role_id, email, user_name, current_user, form_data_dict)
        
        if not billing_result["success"]:
            return False, f"Billing error: {billing_result['error']}"
        
        # Return billing information instead of creating user
        return "billing_required", billing_result


def create_user_without_billing(form_data: list):
    """
    Create a user without billing (for clients or after payment is completed).
    """
    print(f"DEBUG: create_user_without_billing called with form_data: {form_data}")
    (first_name, last_name, email, client_id, role, phone, title, password) = form_data
    print(f"DEBUG: Parsed data - first_name: {first_name}, last_name: {last_name}, email: {email}, client_id: {client_id}, role: {role}")
    # Generate username from email, first name and lastname
    username = generate_unique_username(get_base_user_str(email, first_name, last_name))
    form_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "title": title,
        "username": username,
        "password": password,
        "password_needs_change": True,
    }

    try:
        with transaction.atomic():
            user = UserManager.create_user(**form_data)
            if int(role) == CLIENT_ROLE:
                company = ClientCompany.objects.get(pk=client_id)
                UserManager.create_client_user(user, company=company)
                group = Group.objects.get(name='Client')
                user.groups.add(group.pk)
            else:
                tech_user = UserManager.create_technician_user(user)
                if tech_user:
                    # Use the role ID directly to get the group instead of trying to match by name
                    try:
                        group = Group.objects.get(id=int(role))
                        user.groups.add(group)
                    except Group.DoesNotExist:
                        print(f"Group with ID {role} not found")
                        return False, f"Role with ID {role} not found"

    except Exception as e:
        print("False returned, didn't save")
        print(f"DEBUG: Exception details: {str(e)}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")
        return False, str(e)

    return True, ""


def assign_client_main_tech(client_id, user):
    """
    Assign the main technician to a client company.

    This function assigns a given user as the main technician for a specified client company. It handles the case where the client company does not exist.

    Args:
        client_id (int): The ID of the client company.
        user (TechnicianUser): The user to be assigned as the main technician.

    Raises:
        ClientCompany.DoesNotExist: If the client company with the given ID does not exist.
    """
    try:
        client = ClientCompany.objects.get(pk=client_id)
        client.main_tech = user
        client.save()
        print(f"Updated client {client_id} with main tech {user}")
    except ClientCompany.DoesNotExist:
        print(f"Client with ID {client_id} does not exist")


def process_form_data_sets(form_data_sets, current_user=None):
    """
    Process each set of form data and create users.

    Iterates over each set of form data, attempts to create a user, and collects
    error messages for any unsuccessful creations.

    Args:
        form_data_sets (zip): A zip object containing tuples of form data.
        current_user: The user creating the accounts (to determine company's subscription tier)

    Returns:
        tuple: A tuple containing the number of unsuccessful creations and
               a concatenated string of error messages, or billing information.
    """
    unsuccessful_creations = 0
    error_message = ""
    billing_sessions = []

    for form_data in form_data_sets:
        result = create_user(form_data, current_user)

        
        if isinstance(result, tuple):
            if result[0] == "billing_required":
                # This is a billing requirement, not an error
                billing_sessions.append(result[1])  # result[1] contains the billing result
            else:
                is_success, error = result
                if not is_success:
                    unsuccessful_creations += 1
                    error_message += error
        else:
            # Handle billing result
            billing_sessions.append(result)

    if billing_sessions:
        # Return billing information
        return "billing_required", billing_sessions
    
    return unsuccessful_creations, error_message


# ########################################
# User Profile Settings Page
def get_context_data(user):
    """
    Generate context data for the user profile settings page.

    This function retrieves the user's webviews and, if the user is a superuser,
    fetches a list of clients that do not have a main technician assigned.

    Args:
        user (User): The user object for whom the context data is generated.

    Returns:
        dict: A dictionary containing the context data for rendering the profile settings page.
    """
    context = {"user": user, "webviews": WebviewIntegrations.objects.filter(user=user)}
    
    # Add company subscription tier (default to starter)
    context["company_subscription_tier"] = "starter"
    
    if user.is_superuser:
        # Only an admin can create users, we need to fetch clients only for user creation
        context["clients"] = list(ClientCompany.objects.all().values("name", "id"))
        
        # Add user lists for the New Account Creation tab
        from accounts.models import MSPAuthUser, TechnicianUser
        from apps.models import ClientUser
        
        # Get the Client group ID
        from django.contrib.auth.models import Group
        try:
            client_group = Group.objects.get(name='Client')
            client_group_id = client_group.id
        except Group.DoesNotExist:
            client_group_id = None
        
        # Get all non-client users (users not in Client group)
        if client_group_id:
            non_client_users = MSPAuthUser.objects.exclude(
                groups__id=client_group_id
            ).prefetch_related('groups')
        else:
            # Fallback: get users with technician profiles
            non_client_users = MSPAuthUser.objects.filter(
                technician__isnull=False
            ).select_related('technician').prefetch_related('groups')
        
        # Get all client users (users in Client group)
        if client_group_id:
            client_users = MSPAuthUser.objects.filter(
                groups__id=client_group_id
            ).prefetch_related('groups')
        else:
            # Fallback: get users with client profiles
            client_users = MSPAuthUser.objects.filter(
                client__isnull=False
            ).select_related('client').prefetch_related('groups')
        
        context["non_client_users"] = non_client_users
        context["client_users"] = client_users
    
    return context


def process_profile_update_form(request, user):
    """
    Process the profile update form.

    This function validates the form data, updates the user instance with the cleaned data,
    saves the instance, and handles any error messages that may arise during the validation.

    Args:
        request (HttpRequest): The HTTP request object containing form data.
        user (User): The user instance being updated.

    Returns:
        TechnicianUserUpdateForm: The form instance, which may contain validation errors.
    """
    form = MSPAuthUserForm(request.POST, request.FILES, instance=user)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.password_needs_change = False
        instance.save()
        messages.success(request, "Successfully Updated User Profile")

    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    return form




