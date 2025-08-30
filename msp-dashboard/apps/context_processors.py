# Python Imports
from datetime import datetime, timezone
from django.utils import timezone as django_timezone
# Django imports
from django.shortcuts import get_object_or_404

from .models import TechnicianLabor, TicketList, WebviewIntegrations

# Context Processors
def active_entry(request):
    if request.user.is_authenticated and hasattr(request.user, 'technician'):
        untracked_labor = TechnicianLabor.objects.filter(created_by=request.user.technician, minutes=0, is_tracked=False)
        
        if untracked_labor:
            active_entry = untracked_labor.first()
            active_entry.seconds_since = int((django_timezone.now() - active_entry.created_at).total_seconds())
            
            return {'active_entry_seconds':active_entry.seconds_since,
                    'start_time':active_entry.created_at.isoformat()}

    return {'active_entry_seconds':0, 'start_time':django_timezone.now().isoformat()}

def integrations(request):
    if request.user.is_authenticated:
        webview_integrations = WebviewIntegrations.objects.filter(user=request.user)
    else:
        webview_integrations = "Log In!"
    return {
        'webview' : webview_integrations
    }