from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, date
import recurrence
from recurrence import Recurrence, Rule

from .models import CalendarEvents
from apps.models import TechnicianUser

RECURRENCE_CHOICES = {'DAILY': recurrence.DAILY,
    'WEEKLY': recurrence.WEEKLY,
    'MONTHLY': recurrence.MONTHLY,
    'YEARLY': recurrence.YEARLY,
}

WEEKDAY_CHOICES = {
        'MONDAY': 0,
        'TUESDAY': 1,
        'WEDNESDAY': 2,
        'THURSDAY': 3,
        'FRIDAY': 4,
        'SATURDAY': 5,
        'SUNDAY': 6,
}

BG_COLOUR_MAPPING = {
    'Danger':'#ed5e5e',
    'Dark':'#363D48',
    'Info':'#50c3e6',
    'Primary':'#6691e7',
    'Success':'#13c56b',
    'Warning':'#e8bc52',
}

COLOUR_MAPPING = {
    'Danger':'#ed5e5e',
    'Dark':'#363D48',
    'Info':'#50c3e6',
    'Primary':'#6691e7',
    'Success':'#13c56b',
    'Warning':'#e8bc52',
}

CLASSNAME_MAPPING = {
    "Danger": "bg-soft-danger",
    "Success": "bg-soft-success",
    "Primary": "bg-soft-primary",
    "Info": "bg-soft-info",
    "Dark": "bg-soft-dark",
    "Warning": "bg-soft-warning",
}

class CalendarEventSerializer(serializers.ModelSerializer):
    guest_emails = serializers.ListField(child=serializers.CharField(required=False), required=False)
    is_creator = serializers.SerializerMethodField()
    guest_list = serializers.SerializerMethodField()
    textColor = serializers.SerializerMethodField()
    backgroundColor = serializers.SerializerMethodField()
    dateRange = serializers.SerializerMethodField()
    className = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()


    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super(CalendarEventSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    class Meta:
        model = CalendarEvents
        fields = ['id', 'title', 'type', 'description', 'location', 'start', 'end', 'guest_list',
                'is_creator', 'recurrence', 'guest_emails', 'textColor', 'repeating', 'event_last_date',
                'dateRange', 'backgroundColor', 'className']

    @staticmethod
    def get_list_fields():
        return ['id', 'title', 'type', 'description', 'location', 'start', 'end', 'guest_list',
                'is_creator', 'recurrence', 'guest_emails', 'textColor', 'repeating', 'event_last_date',
                'dateRange', 'className']
    
    def get_title(self, CalendarEvents):
        return CalendarEvents.name

    def get_is_creator(self, CalendarEvents):
        request = self.context['request']
        return True if request.user == CalendarEvents.creator else False

    def get_guest_list(self, CalendarEvents):
        # instead of returning list of guest emails, also return their ids
        return [{"email": guest.email, "user_id": str(guest.user_id)} for guest in CalendarEvents.guests.all()] if CalendarEvents.guests else []

    def get_textColor(self, CalendarEvents):
        return COLOUR_MAPPING[CalendarEvents.type] if CalendarEvents.type else None

    def get_backgroundColor(self, CalendarEvents):
        return BG_COLOUR_MAPPING[CalendarEvents.type] if CalendarEvents.type else None

    def get_className(self, CalendarEvents):
        return CLASSNAME_MAPPING[CalendarEvents.type] if CalendarEvents.type else "bg-soft-info"

    def get_dateRange(self, CalendarEvents):
        dateRange = []
        try:
            if CalendarEvents.recurrence:
                for occurrence in CalendarEvents.recurrence.occurrences():
                    start = datetime.combine(occurrence.date(), occurrence.time())
                    end = datetime.combine(occurrence.date(), CalendarEvents.end.time())
                    if start == end:
                        continue
                    dateRange.append({
                        "start" : start,
                        "end" : end
                    })
        except Exception as e:
            pass
        return dateRange


    def set_recurrance_rule(self, validated_data):
        start = validated_data.get('start', None)
        end = validated_data.get('end', None)
        event_last_date = validated_data.get('event_last_date')
        if isinstance(event_last_date, date):
            event_last_date = event_last_date.strftime("%Y-%m-%d")
        frequency = validated_data.get("repeat_frequency", "DAILY")
        interval = validated_data.get("repeat_interval", 1)
        repeat_by_weekdays = validated_data.get("repeat_by_weekdays", [])

        if event_last_date and event_last_date < start:
            raise Exception("End date cannot be before start date.")

        if end and event_last_date:
            event_last_date = datetime.combine(
                datetime.strptime(event_last_date, "%Y-%m-%d"),
                datetime.strptime(end, "%Y-%m-%dT%H:%M:%S.%fZ").time())

        recurrence_rule = Rule(
                freq = RECURRENCE_CHOICES[frequency],
                interval = interval,
                byday=repeat_by_weekdays,
                )
        limits = Recurrence(
                dtstart= datetime.strptime(start, "%Y-%m-%dT%H:%M:%S.%fZ") if start else timezone.now(),
                dtend= event_last_date,
                rrules=[recurrence_rule]
            )

        return limits

    def create(self, validated_data):
        request = self.context['request']
        guest_emails = request.data.pop('guest_emails', None)
        repeat_by_weekdays = request.data.pop("repeat_by_weekdays", [])
        request.data['creator'] = request.user

        if not request.data.get('event_last_date', None):
            request.data['event_last_date'] = datetime.strptime(request.data['end'], "%Y-%m-%dT%H:%M:%S.%fZ").date()

        # Handle Recurring events
        try:
            if request.data.get("repeating", False):
                request.data['repeat_by_weekdays'] = [WEEKDAY_CHOICES[day] for day in repeat_by_weekdays if day != "ALL"]
                limits = self.set_recurrance_rule(request.data)
                request.data["recurrence"] = limits

            event = super().create(request.data)
            if guest_emails:
                for guest_email in guest_emails:
                    try:
                        if guest_email != "null":
                            guest = TechnicianUser.objects.get(email__icontains = guest_email)
                            if not guest in event.guests.all():
                                event.guests.add(guest)
                    except:
                        raise Exception(f"{guest_email} is not a valid user.")
            return event
        except Exception as e:
            raise ValidationError({"error": [e]})

    def update(self, instance, validated_data):
        request = self.context['request']
        guest_emails = request.data.pop('guest_emails', None)
        repeat_by_weekdays = request.data.pop("repeat_by_weekdays", [])
        request.data['creator'] = request.user

        # Handle Recurring events
        try:
            if request.data.get("repeating", False):
                request.data['repeat_by_weekdays'] = [WEEKDAY_CHOICES[day] for day in repeat_by_weekdays if day != "ALL"]
                limits = self.set_recurrance_rule(request.data)
                request.data["recurrence"] = limits

            event = super().update(instance, request.data)
            if guest_emails:
                event.guests.clear()
                for guest_email in guest_emails:
                    try:
                        if guest_email != "null":
                            guest = TechnicianUser.objects.get(email__icontains = guest_email)
                            if not guest in event.guests.all():
                                event.guests.add(guest.technician_id)
                    except:
                        raise Exception(f"{guest_email} is not a valid user.")
            return event
        except Exception as e:
            raise ValidationError({"error": [e]})
