from .forms import CalendarEventForm
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets
from django.utils import timezone
from datetime import datetime, timedelta
import datetime as dt
from django.db.models import Q
from accounts.models import TechnicianUser

from .models import CalendarEvents, WEEKDAY_CHOICES
from .serializers import CalendarEventSerializer

class AppsView(LoginRequiredMixin,TemplateView):
    pass

apps_calendar_view = AppsView.as_view(template_name="apps/apps-calendar.html")


def parse_datetime(date_str):
    try:
        # Remove the timezone description (e.g., "(Pakistan Standard Time)")
        clean_date_str = date_str.split(' (')[0]
        dt = datetime.strptime(clean_date_str, '%a %b %d %Y %H:%M:%S %Z%z')
        return dt.isoformat()
    except ValueError as e:
        print(f"Error parsing date: {e}")
        return None

def handle_date(field, post_data):
    date_value = parse_datetime(field)
    if date_value:
        return date_value
    elif not post_data.get('eventid'):
        return None
    return field


def handle_calendar_event(post_data):
    # Parse 'start' and 'end' datetime fields
    start = post_data.pop('start')[0]
    end = post_data.pop('end')[0]

    if start:
        post_data['start'] = handle_date(start, post_data)
    if end:
        post_data['end'] = handle_date(end, post_data)
    
    # Check if 'guests' field is in POST data and has empty values
    if 'guests' in post_data:
        # Convert the 'guests' field into a list and remove empty values
        guests_list = [guest for guest in post_data.getlist('guests') if guest]  # Remove empty values
        
        # If there are no valid guests, remove the field
        if not guests_list:
            post_data.pop('guests', None)  # Remove the 'guests' field if empty
        else:
            # Update the POST data with cleaned guests list
            post_data.setlist('guests', guests_list)


    return post_data

def handle_repeated_events(post_data):
     # Extract the repeat settings if this is a repeating event
    try:
        
        # Map days to integers based on your WEEKDAY_CHOICES
        # Convert the days to integers and save to post_data
        repeat_by_weekdays = [WEEKDAY_CHOICES[day] for day in post_data.getlist('repeat_by_weekdays') if day in WEEKDAY_CHOICES]
        post_data.setlist('repeat_by_weekdays', repeat_by_weekdays)

        # If you have a complex recurrence pattern, set `recurrence` accordingly
        # This depends on how you want to handle recurrence logic; you can use a library
        # or custom logic to generate recurrence rules and save them in the `RecurrenceField`.
        # For simplicity, we're not setting `recurrence` here.
    
    except (ValueError, KeyError) as e:
        print("Error parsing repeat settings:", e)

    return post_data
    

def apps_calendar_view_delete(request):
    if request.POST:
        eventid = request.POST.get('delete-event-id')
        CalendarEvents.objects.get(pk=eventid).delete()
        # messages.suce
    return redirect("calendar_event:calendar-events")

def apps_calendar_view(request):
    events = CalendarEvents.objects.filter(creator=request.user)
    technicians = TechnicianUser.objects.all()

    # Serialize the events data
    events = CalendarEventSerializer(events, many=True, context={'request': request}).data

    if request.method == 'POST':
        # Preprocess the POST data to remove empty 'guests' field values
        clean_form = request.POST.copy()
        clean_form['creator'] = request.user
        eventid = clean_form.get('eventid')

        print(clean_form)
        print("\n\n")
        #? Clean Submitted form, calculation and more
        clean_form = handle_calendar_event(clean_form)

        print(clean_form)

        # If eventid is passed, it means it's a request to update
        instance = CalendarEvents.objects.get(pk=eventid) if eventid else None
        if instance:
            if not clean_form.get('start'): 
                clean_form['start'] = instance.start
            if not clean_form.get('end'): 
                clean_form['end'] = instance.end
        form = CalendarEventForm(clean_form, instance=instance)

        if form.is_valid():
            instance = form.save()
            print(instance)
            return redirect("calendar_event:calendar-events")
        else:
            print(form.errors)

    return render(request, "apps/apps-calendar.html", context={'events': events, 'technicians': technicians})

def apps_calendar_edit_view(request, pk):
    print("EDIT")
    events = CalendarEvents.objects.filter(creator=request.user)
    if request.method == 'POST':
        event = events.filter(creator=request.user, pk=pk)
        form = CalendarEventForm(request.POST, instance=event)
        if form.is_valid():
            return redirect("calendar_event:calendar-events-edit")
        else:
            pass
    return render(request, "apps/apps-calendar.html", context={'events': events})


class CalendarEventViewSet(viewsets.ModelViewSet):
    queryset = CalendarEvents.objects.all()
    serializer_class = CalendarEventSerializer

    def get_queryset(self):
        print(self.request.user)
        if self.request.query_params.get('date'):
            date_str = self.request.query_params.get('date')
            date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
            queryset = CalendarEvents.objects.filter(
                Q(start__lte=date, end__gte = date) |
                Q(recurrence__contains=date.strftime('%m-%d'))
            )
            queryset = queryset.filter(
                Q(creator = self.request.user.user_id) |
                Q(guests__user_id__contains = self.request.user.user_id)
            )
            return queryset
        elif self.request.query_params.get('month'):
            month = self.request.query_params.get('month')
            year = int(self.request.query_params.get('year'))
            start_date = dt.date(year, int(month), 1)
            end_date = dt.date(year, int(month)+1, 1) - timedelta(days=1)
            queryset = CalendarEvents.objects.filter(
                Q(start__date__lte=end_date, event_last_date__gte=start_date)
            )
            queryset = queryset.filter(
                Q(creator = self.request.user.user_id) |
                Q(guests__user_id__contains = self.request.user.user_id)
            )
            return queryset
        else:
            if not hasattr(self.request.user, 'technician') :
                return CalendarEvents.objects.none()
            user = self.request.user
            calendar_events = CalendarEvents.objects.filter(
                Q(creator = user.user_id) |
                Q(guests__user_id__contains = user.user_id)
            )
            return calendar_events

    def get_serializer(self, *args, **kwargs):
        if self.action == "list":
            kwargs["fields"] = self.serializer_class().get_list_fields()
        return super().get_serializer(*args, **kwargs)


@api_view(['POST', 'GET'])
def calendar_function_view(request):

    user = request.user  # Access the logged-in user
    if user.is_authenticated:
        # User is logged in, you can now access user details
        print(f"User: {user.username}")
        print(f"Request Body: {request.data}")  # Access request data
        return Response({'success': True, 'user': user.username})
    else:
        # User is not authenticated
        return Response({'error': 'User not authenticated'}, status=401)
    