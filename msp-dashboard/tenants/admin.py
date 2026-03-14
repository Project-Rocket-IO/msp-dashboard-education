from django import forms
from django.contrib import admin

from .models import MspCompany


class MspCompanyAdminForm(forms.ModelForm):
    class Meta:
        model = MspCompany
        fields = "__all__"
        widgets = {
            "entra_id_client_secret": forms.PasswordInput(render_value=False),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.entra_id_client_secret:
            self.fields["entra_id_client_secret"].help_text = (
                "Leave blank to keep the current client secret."
            )

    def clean_entra_id_client_secret(self):
        secret = self.cleaned_data.get("entra_id_client_secret")
        if secret:
            return secret
        if self.instance and self.instance.pk:
            return self.instance.entra_id_client_secret
        return secret


@admin.register(MspCompany)
class MspCompanyAdmin(admin.ModelAdmin):
    form = MspCompanyAdminForm
    list_display = [
        "company_name",
        "schema_name",
        "enable_entra_id_auth",
        "entra_id_ready",
    ]
    readonly_fields = ["entra_id_callback_url"]
    search_fields = ["company_name", "schema_name", "email"]

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if "entra_id_callback_url" not in fields:
            try:
                insert_at = fields.index("entra_id_client_secret_id") + 1
            except ValueError:
                insert_at = len(fields)
            fields.insert(insert_at, "entra_id_callback_url")
        return fields

    @admin.display(boolean=True, description="Entra ID ready")
    def entra_id_ready(self, obj):
        return obj.is_entra_id_configured

    @admin.display(description="Entra ID callback URL")
    def entra_id_callback_url(self, obj):
        if obj is None or not obj.pk:
            return "Save the tenant to generate its callback URL."
        return obj.get_entra_id_callback_url()