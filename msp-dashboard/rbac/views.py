from django.shortcuts import redirect, render, reverse
from dashboards.views import (
    dashboard_analytics_view
)
from apps.access import user_should_land_in_ticket_list

def view_home(request):
    user = request.user
    if user_should_land_in_ticket_list(user):
        return redirect(reverse('apps:tickets.list'))
    return dashboard_analytics_view(request)
