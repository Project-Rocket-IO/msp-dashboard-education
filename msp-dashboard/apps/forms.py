import re
from phonenumber_field.phonenumber import to_python
from phonenumber_field.formfields import PhoneNumberField
from django import forms
from projectRocket import settings
from .models import (
    ClientUser,
    ClientCompany,
    TechnicianUser,
    TicketList,
    ProjectList,
    TicketComment,
    ProjectComment,
    TicketCommentReplies,
    ProjectCommentReplies,
    LeadCompany,
    TechnicianLabor,
    WebviewIntegrations,
    ProjectFiles,
    LeadOpportunity,
    ClientLocations,
    ClientTeamMembers,
    SalesRequests,
    APIIntegrations,
    ClientWorkTypeRate,
    QuickBooksCustomer,
)


class CleanPhoneFaxParent:
    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        # Reuse the validator logic here
        if phone:
            if re.match(r"^\+\d{1,4}$", str(phone)):
                return ""  # Remove the phone number if it's just the international code

        return (
            phone  # Return the validated phone number if it doesn't match the criteria
        )

    def clean_fax(self):
        fax = self.cleaned_data.get("fax")
        # Reuse the validator logic here
        if fax:
            if re.match(r"^\+\d{1,4}$", str(fax)):
                return ""  # Remove the fax number if it's just the international code

        return fax


class LeadCompanyAddForm(forms.ModelForm, CleanPhoneFaxParent):
    class Meta:
        model = LeadCompany
        fields = "__all__"


class LeadCompanyUpdateForm(forms.ModelForm, CleanPhoneFaxParent):
    class Meta:
        model = LeadCompany
        fields = "__all__"


class ClientCompanyAddForm(forms.ModelForm, CleanPhoneFaxParent):
    class Meta:
        model = ClientCompany
        exclude = ["threshold"]
        fields = "__all__"


class ClientCompanyUpdateForm(forms.ModelForm, CleanPhoneFaxParent):

    class Meta:
        model = ClientCompany
        fields = "__all__"
        exclude = ["main_tech", "threshold"]


class ClientLocationsAddForm(forms.ModelForm):
    class Meta:
        model = ClientLocations
        fields = "__all__"


class ClientTeamMembersAddForm(forms.ModelForm):
    class Meta:
        model = ClientTeamMembers
        fields = "__all__"


class TicketListAddForm(forms.ModelForm):
    assignment = forms.ModelMultipleChoiceField(
        queryset=TechnicianUser.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = TicketList
        fields = [
            "logo",
            "name",
            "description",
            "assignment",
            "end_date",
            "client",
            "due_date",
            "project",
            "ticket_type",
            "status",
            "priority",
            "tag"
        ]


class ProjectFileForm(forms.ModelForm):
    class Meta:
        model = ProjectFiles
        fields = ["file"]


class ProjectListAddForm(forms.ModelForm):
    tickets = forms.ModelMultipleChoiceField(
        queryset=TicketList.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = ProjectList
        fields = [
            "logo",
            "name",
            "description",
            "assignment",
            "tickets",
            "end_date",
            "due_date",
            "status",
            "priority",
            "client",
            "tag",
        ]


class TicketCommentAddForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = "__all__"


class TicketCommentUpdateForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ["body"]


class TicketRepliesAddForm(forms.ModelForm):
    class Meta:
        model = TicketCommentReplies
        fields = ["body", "user", "comment", "ticket"]


class ProjectRepliesAddForm(forms.ModelForm):
    class Meta:
        model = ProjectCommentReplies
        fields = ["body", "user", "comment", "project"]


class ProjectCommentAddForm(forms.ModelForm):
    class Meta:
        model = ProjectComment
        fields = "__all__"


class TechnicianLaborAddForm(forms.ModelForm):
    created_at = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'text', 'data-provider': 'flatpickr', 'data-date-format': 'Y-m-d'}),
        help_text="Select the date when the work was performed"
    )
    
    class Meta:
        model = TechnicianLabor
        fields = ["minutes", "created_at", "comment", "created_by"]
    
    def clean_created_at(self):
        date_value = self.cleaned_data.get('created_at')
        if date_value:
            # Convert date to timezone-aware datetime
            from django.utils import timezone
            from datetime import datetime
            # Create a datetime at midnight in the current timezone
            return timezone.make_aware(datetime.combine(date_value, datetime.min.time()))
        return date_value


class WebviewIntegrationsAddForm(forms.ModelForm):
    class Meta:
        model = WebviewIntegrations
        fields = "__all__"


class WebviewIntegrationsUpdateForm(forms.ModelForm):
    class Meta:
        model = WebviewIntegrations
        fields = "__all__"


class LeadOpportunityAddForm(forms.ModelForm):
    class Meta:
        model = LeadOpportunity
        fields = "__all__"


class SalesRequestsAddForm(forms.ModelForm):
    # Override the due_date field to be more permissive
    due_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'text'}))
    
    class Meta:
        model = SalesRequests
        fields = "__all__"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(f"DEBUG: SalesRequestsAddForm initialized with data: {args}")
        if args and len(args) > 0:
            print(f"DEBUG: POST data: {args[0]}")
            if 'due_date' in args[0]:
                print(f"DEBUG: due_date in POST: '{args[0]['due_date']}'")
    
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        print(f"DEBUG: clean_due_date received: '{due_date}' (type: {type(due_date)})")
        
        # Allow None/empty values for due_date since it's optional
        if due_date == '' or due_date is None:
            print("DEBUG: Returning None for empty/None value")
            return None
        # If it's a string, try to parse it
        if isinstance(due_date, str) and due_date.strip() == '':
            print("DEBUG: Returning None for empty string")
            return None
        # Handle the case where "None" is passed as a string
        if isinstance(due_date, str) and due_date.strip().lower() == 'none':
            print("DEBUG: Returning None for 'None' string")
            return None
        # If it's a string that's not empty and not "None", try to validate it
        if isinstance(due_date, str) and due_date.strip() != '' and due_date.strip().lower() != 'none':
            try:
                from datetime import datetime
                # Try to parse the date string
                parsed_date = datetime.strptime(due_date.strip(), '%Y-%m-%d').date()
                print(f"DEBUG: Parsed date: {parsed_date}")
                return parsed_date
            except ValueError:
                print(f"DEBUG: Failed to parse date: '{due_date}'")
                raise forms.ValidationError("Enter a valid date in YYYY-MM-DD format.")
        print(f"DEBUG: Returning original value: {due_date}")
        return due_date


class APIIntegrationsAddForm(forms.ModelForm):
    class Meta:
        model = APIIntegrations
        fields = "__all__"


class ClientUserForm(forms.ModelForm):
    class Meta:
        model = ClientUser
        fields = "__all__"


class ClientWorkTypeRateAddForm(forms.ModelForm):
    class Meta:
        model = ClientWorkTypeRate
        fields = "__all__"


class ClientWorkTypeRateUpdateForm(forms.ModelForm):
    class Meta:
        model = ClientWorkTypeRate
        fields = ["name", "rate"]
