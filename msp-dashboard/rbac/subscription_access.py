from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from functools import wraps
from django.conf import settings
import django_tenants.utils


def require_subscription_feature(feature_name):
    """
    Decorator to check if the current tenant has access to a specific feature
    based on their subscription tier.
    
    Usage:
    @require_subscription_feature('leads')
    def my_view(request):
        # Only accessible if tenant has leads feature
        pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Get the current tenant
            tenant = getattr(request, 'tenant', None)
            
            if not tenant:
                # If no tenant, allow access (for non-tenant contexts)
                return view_func(request, *args, **kwargs)
            
            # Check if tenant has access to the feature
            if hasattr(tenant, 'has_feature_access') and tenant.has_feature_access(feature_name):
                return view_func(request, *args, **kwargs)
            else:
                # Feature not available for this subscription tier
                messages.error(
                    request, 
                    f"This feature ({feature_name.title()}) is not available in your current subscription tier. "
                    f"Please upgrade your subscription to access this feature."
                )
                return redirect('payments:payments.payments')
        
        return _wrapped_view
    return decorator


def subscription_feature_required(feature_name):
    """
    Alternative decorator that returns 403 Forbidden instead of redirecting
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            tenant = getattr(request, 'tenant', None)
            
            if not tenant:
                return view_func(request, *args, **kwargs)
            
            if hasattr(tenant, 'has_feature_access') and tenant.has_feature_access(feature_name):
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden(
                    f"Access denied. Feature '{feature_name}' is not available in your subscription tier."
                )
        
        return _wrapped_view
    return decorator


def get_available_features(tenant):
    """
    Get list of available features for a tenant based on their subscription tier
    """
    if not tenant or not hasattr(tenant, 'get_subscription_tier'):
        return []
    
    tier = tenant.get_subscription_tier()
    
    feature_access = {
        'starter': ['dashboard', 'tickets', 'projects', 'clients', 'invoicing', 'calendar'],
        'growth': ['dashboard', 'tickets', 'projects', 'clients', 'invoicing', 'calendar', 'leads', 'sales'],
        'innovator': ['dashboard', 'tickets', 'projects', 'clients', 'invoicing', 'calendar', 'leads', 'sales', 'atlas']
    }
    
    return feature_access.get(tier, [])


def check_feature_access(request, feature_name):
    """
    Utility function to check if current user has access to a feature
    """
    tenant = getattr(request, 'tenant', None)
    
    if not tenant:
        return True  # Allow access in non-tenant contexts
    
    return hasattr(tenant, 'has_feature_access') and tenant.has_feature_access(feature_name) 