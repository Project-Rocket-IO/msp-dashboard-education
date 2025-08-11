from django.shortcuts import redirect, render, reverse
from dashboards.views import (
    dashboard_analytics_view
)

def view_home(request):
    user = request.user
    if hasattr(user, 'client'):
        print("CLIENT HE")
        return redirect(reverse('apps:tickets.list'))
    return dashboard_analytics_view(request)
