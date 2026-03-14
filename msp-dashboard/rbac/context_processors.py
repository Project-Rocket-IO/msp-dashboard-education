from django.conf import settings

from apps.access import user_can_access_dashboard, user_should_land_in_ticket_list
from rbac.subscription_access import check_feature_access, get_available_features


def subscription_context(request):
    """
    Context processor to make subscription information available in templates
    """
    context = {}
    
    # Get current tenant (company)
    tenant = getattr(request, 'tenant', None)
    
    if tenant:
        # Add company's subscription tier info
        context['subscription_tier'] = tenant.get_subscription_tier()
        context['available_features'] = get_available_features(tenant)
        
        # Add feature access checks based on company's subscription
        context['has_dashboard_access'] = (
            check_feature_access(request, 'dashboard')
            and user_can_access_dashboard(getattr(request, 'user', None))
        )
        context['has_tickets_access'] = check_feature_access(request, 'tickets')
        context['has_projects_access'] = check_feature_access(request, 'projects')
        context['has_clients_access'] = check_feature_access(request, 'clients')
        context['has_invoicing_access'] = check_feature_access(request, 'invoicing')
        context['has_calendar_access'] = check_feature_access(request, 'calendar')
        context['has_leads_access'] = check_feature_access(request, 'leads')
        context['has_sales_access'] = check_feature_access(request, 'sales')
        context['has_atlas_access'] = check_feature_access(request, 'atlas')
        
        # Add company subscription info
        context['company_subscription_tier'] = tenant.get_subscription_tier()
        context['company_subscription_name'] = {
            'starter': 'Starter Tier',
            'growth': 'Growth Tier', 
            'innovator': 'Innovator Tier'
        }.get(tenant.get_subscription_tier(), 'Starter Tier')
        
        # Always accessible features (regardless of subscription tier)
        context['has_billing_access'] = True
        context['has_profile_settings_access'] = True
        context['has_help_center_access'] = True
        context['has_file_system_access'] = True
    else:
        # Default values for non-tenant contexts
        context['subscription_tier'] = 'starter'
        context['company_subscription_tier'] = 'starter'
        context['company_subscription_name'] = 'Starter Tier'
        context['available_features'] = ['dashboard', 'tickets', 'projects', 'clients', 'invoicing', 'calendar']
        context['has_dashboard_access'] = user_can_access_dashboard(
            getattr(request, 'user', None)
        )
        context['has_tickets_access'] = True
        context['has_projects_access'] = True
        context['has_clients_access'] = True
        context['has_invoicing_access'] = True
        context['has_calendar_access'] = True
        context['has_leads_access'] = False
        context['has_sales_access'] = False
        context['has_atlas_access'] = False
        
        # Always accessible features
        context['has_billing_access'] = True
        context['has_profile_settings_access'] = True
        context['has_help_center_access'] = True
        context['has_file_system_access'] = True

    context['entra_password_change_url'] = settings.ENTRA_PASSWORD_CHANGE_URL
    context['home_redirects_to_tickets'] = user_should_land_in_ticket_list(
        getattr(request, 'user', None)
    )
    
    return context 
