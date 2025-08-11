from .models import CalendarEvents
from django.forms import ModelForm



class CalendarEventForm(ModelForm):
    class Meta:
        model = CalendarEvents
        fields = "__all__"
