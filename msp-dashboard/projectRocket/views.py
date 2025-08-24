from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from allauth.account.views import PasswordSetView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash

class MyPasswordChangeView(PasswordChangeView):
    success_url = reverse_lazy("home")
    template_name = "account/password_change.html"

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, self.request.user)
        messages.success(self.request, "Password successfully changed.")
        return super().form_valid(form)

class MyPasswordSetView(PasswordSetView):
    success_url = reverse_lazy("home")
    template_name = "account/password_set.html"

def handler403(request, exception=None):
    """Custom 403 error handler"""
    return render(request, '403.html', status=403)