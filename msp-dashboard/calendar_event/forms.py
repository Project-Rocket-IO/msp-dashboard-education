from .models import CalendarEvents
from django.forms import ModelForm



class CalendarEventForm(ModelForm):
    class Meta:
        model = CalendarEvents
        fields = ['name', 'type', 'description', 'location', 'start', 'end', 'creator', 'repeating', 'repeat_interval', 'repeat_frequency', 'repeat_by_weekdays', 'recurrence']
        # Note: mandatory_invites, optional_invites, and guests are handled manually in the view
