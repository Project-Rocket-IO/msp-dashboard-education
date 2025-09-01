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

# apps_calendar_view = AppsView.as_view(template_name="apps/apps-calendar.html")  # REMOVED - conflicts with function view below


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
    start = post_data.pop('start')[0] if 'start' in post_data else ''
    end = post_data.pop('end')[0] if 'end' in post_data else ''

    if start:
        post_data['start'] = handle_date(start, post_data)
    elif 'start_date' in post_data and 'start_time' in post_data:
        # Combine start_date and start_time when start is empty
        start_date = post_data.get('start_date', '')
        start_time = post_data.get('start_time', '')
        if start_date and start_time:
            post_data['start'] = f"{start_date} {start_time}:00"
    
    if end:
        post_data['end'] = handle_date(end, post_data)
    elif 'end_date' in post_data and 'end_time' in post_data:
        # Combine end_date and end_time when end is empty
        end_date = post_data.get('end_date', '')
        end_time = post_data.get('end_time', '')
        if end_date and end_time:
            post_data['end'] = f"{end_date} {end_time}:00"
    
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
    # Get events where user is creator OR attendee (mandatory, optional, or guest)
    events = CalendarEvents.objects.filter(
        Q(creator=request.user) |
        Q(mandatory_invites=request.user) |
        Q(optional_invites=request.user) |
        Q(guests=request.user)
    ).distinct()
    
    # Get tickets where user is assigned or has access
    from apps.models import TicketList
    tickets = TicketList.objects.filter(
        due_date__isnull=False
    ).distinct()
    
    print(f"DEBUG: Found {tickets.count()} tickets with due dates")
    for ticket in tickets[:3]:  # Show first 3 for debugging
        print(f"  - Ticket {ticket.identifier}: {ticket.name} (Due: {ticket.due_date}, Type: {type(ticket.due_date)})")
        if ticket.due_date:
            print(f"    Raw due_date: {ticket.due_date}")
            print(f"    ISO format: {ticket.due_date.isoformat()}")
            print(f"    String format: {str(ticket.due_date)}")
    
    # Get projects where user is assigned or has access
    from apps.models import ProjectList
    projects = ProjectList.objects.filter(
        due_date__isnull=False
    ).distinct()
    
    print(f"DEBUG: Found {projects.count()} projects with due dates")
    for project in projects[:3]:  # Show first 3 for debugging
        print(f"  - Project {project.identifier}: {project.name} (Due: {project.due_date}, Type: {type(project.due_date)})")
        if project.due_date:
            print(f"    Raw due_date: {project.due_date}")
            print(f"    ISO format: {project.due_date.isoformat()}")
            print(f"    String format: {str(project.due_date)}")
    
    # Get technicians for attendee selection (same as working ticket form)
    technicians = TechnicianUser.objects.all()
    print(f"DEBUG: Found {technicians.count()} technicians")
    for tech in technicians[:3]:  # Show first 3 for debugging
        print(f"  - {tech.pk}: {tech.auth_user.username}")
    
    # Serialize technicians data for JSON template
    technicians_data = []
    for tech in technicians:
        technicians_data.append({
            'id': tech.pk,
            'pk': tech.pk,
            'username': tech.auth_user.username,
            'email': tech.auth_user.email,
            'auth_user': {
                'username': tech.auth_user.username,
                'email': tech.auth_user.email,
                'user_id': tech.auth_user.user_id
            }
        })

    # Serialize the events data
    events_data = CalendarEventSerializer(events, many=True, context={'request': request}).data
    
    # Add event type identifier to events
    for event in events_data:
        event['event_type'] = 'event'
        event['id'] = f"event_{event['id']}"
    
    # Serialize tickets for the template
    for ticket in tickets:
        ticket_data = {
            'id': f'ticket_{ticket.identifier}',
            'title': f'Ticket: {ticket.name}',
            'type': 'Ticket',
            'description': ticket.description,
            'client': ticket.client.name if ticket.client else None,
            'status': ticket.status,
            'priority': ticket.priority,
            'start': ticket.due_date.isoformat() if ticket.due_date else None,
            'end': ticket.due_date.isoformat() if ticket.due_date else None,
            'mandatory_invites': [{'user_id': tech.auth_user.user_id, 'username': tech.auth_user.username, 'email': tech.auth_user.email} for tech in ticket.assignment.all()],
            'optional_invites': [],
            'event_type': 'ticket'
        }
        print(f"DEBUG: Serialized ticket {ticket.identifier}: {ticket_data['title']} (Start: {ticket_data['start']}, End: {ticket_data['end']})")
        events_data.append(ticket_data)
    
    # Serialize projects for the template
    for project in projects:
        project_data = {
            'id': f'project_{project.identifier}',
            'title': f'Project: {project.name}',
            'type': 'Project',
            'description': project.description,
            'client': project.client.name if project.client else None,
            'status': project.status,
            'priority': project.priority,
            'start': project.due_date.isoformat() if project.due_date else None,
            'end': project.due_date.isoformat() if project.due_date else None,
            'mandatory_invites': [{'user_id': tech.auth_user.user_id, 'username': tech.auth_user.username, 'email': tech.auth_user.email} for tech in project.assignment.all()],
            'optional_invites': [],
            'event_type': 'project'
        }
        events_data.append(project_data)
    
    print(f"DEBUG: Found {len(events_data)} total items to display (events: {len(events)}, tickets: {tickets.count()}, projects: {projects.count()})")
    for item in events_data[:3]:  # Show first 3 for debugging
        print(f"  - {item.get('title', 'No title')} ({item.get('event_type', 'unknown')}) on {item.get('start', 'No start')}")

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

        # Store the invite data before removing it from form validation
        mandatory_invites_data = clean_form.getlist('mandatory_invites') if 'mandatory_invites' in clean_form else []
        optional_invites_data = clean_form.getlist('optional_invites') if 'optional_invites' in clean_form else []
        guests_data = clean_form.getlist('guests') if 'guests' in clean_form else []
        
        # Remove these fields from form data to prevent validation errors
        clean_form.pop('mandatory_invites', None)
        clean_form.pop('optional_invites', None)
        clean_form.pop('guests', None)

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
            
            # Handle many-to-many relationships for invites AFTER form is saved
            if mandatory_invites_data:
                # Convert technician IDs to MSPAuthUser objects
                users = []
                for tech_id in mandatory_invites_data:
                    try:
                        tech = TechnicianUser.objects.get(pk=tech_id)
                        users.append(tech.auth_user)
                    except TechnicianUser.DoesNotExist:
                        pass
                instance.mandatory_invites.set(users)
            
            if optional_invites_data:
                # Convert technician IDs to MSPAuthUser objects
                users = []
                for tech_id in optional_invites_data:
                    try:
                        tech = TechnicianUser.objects.get(pk=tech_id)
                        users.append(tech.auth_user)
                    except TechnicianUser.DoesNotExist:
                        pass
                instance.optional_invites.set(users)
            
            if guests_data:
                instance.guests.set(guests_data)
            
            print(f"Event created successfully: {instance.name} on {instance.start} to {instance.end}")
            print(f"Mandatory invites: {[user.username for user in instance.mandatory_invites.all()]}")
            print(f"Optional invites: {[user.username for user in instance.optional_invites.all()]}")
            return redirect("calendar_event:calendar-events")
        else:
            print(form.errors)

    return render(request, "apps/apps-calendar.html", context={'events': events_data, 'technicians': technicians_data})

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
                Q(guests__user_id__contains = self.request.user.user_id) |
                Q(mandatory_invites__user_id__contains = self.request.user.user_id) |
                Q(optional_invites__user_id__contains = self.request.user.user_id)
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
                Q(guests__user_id__contains = self.request.user.user_id) |
                Q(mandatory_invites__user_id__contains = self.request.user.user_id) |
                Q(optional_invites__user_id__contains = self.request.user.user_id)
            )
            return queryset
        else:
            if not hasattr(self.request.user, 'technician') :
                return CalendarEvents.objects.none()
            user = self.request.user
            calendar_events = CalendarEvents.objects.filter(
                Q(creator = user.user_id) |
                Q(guests__user_id__contains = user.user_id) |
                Q(mandatory_invites__user_id__contains = user.user_id) |
                Q(optional_invites__user_id__contains = user.user_id)
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
    