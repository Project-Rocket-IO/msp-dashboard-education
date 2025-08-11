from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth import update_session_auth_hash
from allauth.account.views import PasswordChangeView, PasswordSetView

class MyPasswordChangeView( PasswordChangeView):
    success_url = reverse_lazy('pages:profile_settings')

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, self.request.user)  # Important to keep the user logged in after password change
        messages.success(self.request, "Password successfully changed.")
        return super().form_valid(form)


class MyPasswordSetView( PasswordSetView):
    success_url = reverse_lazy("dashboards:dashboard_analytics")