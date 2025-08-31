from django.db import models
from django.contrib.postgres.fields import ArrayField
from recurrence.fields import RecurrenceField
import projectRocket.settings as settings
from accounts.models import MSPAuthUser

# Selection  # FOR TYPE
EVENT_CHOICES = (
    ('Danger','Danger'),
    ('Dark','Dark'),
    ('Info','Info'),
    ('Primary','Primary'),
    ('Success','Success'),
    ('Warning','Warning'),
)

RECURRENCE_CHOICES = (
    ('DAILY', 'Daily'),
    ('WEEKLY', 'Weekly'),
    ('BI_WEEKLY', 'Bi-Weekly'),
    ('MONTHLY', 'Monthly'),
    ('ANNUALLY', 'Annually'),
    ('CUSTOM', 'Custom'),
)

WEEKDAY_CHOICES = (   # FOR repeat_by_weekdays
        (0, 'MONDAY'),
        (1, 'TUESDAY'),
        (2, 'WEDNESDAY'),
        (3, 'THURSDAY'),
        (4, 'FRIDAY'),
        (5, 'SATURDAY'),
        (6, 'SUNDAY'),
)

class CalendarEvents(models.Model):
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=50, choices=EVENT_CHOICES, null=True, blank=True)
    name = models.CharField(max_length=145,null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)  # Increased length for online meeting links
    creator = models.ForeignKey(MSPAuthUser, null=True, blank=True, on_delete=models.CASCADE,
                                related_name='event_creator')
    guests = models.ManyToManyField(MSPAuthUser, blank=True, related_name='event_guests')  # General guests
    mandatory_invites = models.ManyToManyField(MSPAuthUser, blank=True, related_name='mandatory_events')  # Required attendees
    optional_invites = models.ManyToManyField(MSPAuthUser, blank=True, related_name='optional_events')  # Optional attendees
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    event_last_date = models.DateField(null=True, blank=True)
    repeating = models.BooleanField(default=False, null=True, blank=True)
    repeat_interval = models.IntegerField(null=True, blank=True)
    repeat_frequency = models.CharField(max_length=20, choices=RECURRENCE_CHOICES, null=True, blank=True)
    repeat_by_weekdays = ArrayField(models.IntegerField(choices=WEEKDAY_CHOICES), default=list, null=True, blank=True)
    recurrence = RecurrenceField(null=True, blank=True, verbose_name="Recurrence")
    
    @property
    def get_guests(self):
        # get all guests and return them as a list
        # return it json format
        return [{'id': guest.user_id, 'username': guest.username, 'email': guest.email} for guest in self.guests.all()]
    
    @property
    def get_mandatory_invites(self):
        # get all mandatory invites and return them as a list
        return [{'id': invite.user_id, 'username': invite.username, 'email': invite.email} for invite in self.mandatory_invites.all()]
    
    @property
    def get_optional_invites(self):
        # get all optional invites and return them as a list
        return [{'id': invite.user_id, 'username': invite.username, 'email': invite.email} for invite in self.optional_invites.all()]
        
    