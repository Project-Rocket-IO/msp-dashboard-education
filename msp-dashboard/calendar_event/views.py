from .forms import CalendarEventForm
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import viewsets
from django.utils import timezone
from datetime import datetime, timedelta
import datetime as dt
from django.db.models import Q
from accounts.models import TechnicianUser
from apps.access import (
    get_visible_projects_queryset,
    get_visible_tickets_queryset,
    user_can_manage_calendar_event,
)

from .models import CalendarEvents, WEEKDAY_CHOICES
from .serializers import CalendarEventSerializer

class AppsView(LoginRequiredMixin,TemplateView):
    pass

# apps_calendar_view = AppsView.as_view(template_name="apps/apps-calendar.html")  # REMOVED - conflicts with function view below


def parse_datetime(date_str):
    try:
        # First try to parse as ISO format (from JavaScript)
        if 'T' in date_str and date_str.endswith('Z'):
            # ISO format with Z timezone
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.isoformat()
        elif 'T' in date_str:
            # ISO format without Z
            dt = datetime.fromisoformat(date_str)
            return dt.isoformat()
        else:
            # Try the old format for backward compatibility
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
    """Handle creating multiple recurring events based on recurrence settings"""
    try:
        # Check if this is a repeating event
        if not post_data.get('repeating'):
            return post_data
            
        # Get recurrence settings
        repeat_frequency = post_data.get('repeat_frequency', 'WEEKLY')
        repeat_interval = int(post_data.get('repeat_interval', 1))
        repeat_ends = post_data.get('repeat_ends', 'never')
        repeat_end_date = post_data.get('repeat_end_date')
        repeat_by_weekdays = post_data.get('repeat_by_weekdays', '')
        
        # Parse the start date to determine the base event date
        start_date_str = post_data.get('start')
        if not start_date_str:
            return post_data
            
        try:
            base_start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        except:
            base_start_date = datetime.fromisoformat(start_date_str)
            
        # Parse the end date
        end_date_str = post_data.get('end')
        if not end_date_str:
            return post_data
            
        try:
            base_end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        except:
            base_end_date = datetime.fromisoformat(end_date_str)
            
        # Calculate the time difference for the event duration
        event_duration = base_end_date - base_start_date
        
        # Determine end date for recurrence
        if repeat_ends == 'on' and repeat_end_date:
            try:
                recurrence_end = datetime.strptime(repeat_end_date, '%Y-%m-%d')
            except:
                recurrence_end = None
        else:
            recurrence_end = None
            
        # Generate recurring events
        events_to_create = []
        current_date = base_start_date
        
        # For weekly recurrence with specific days
        if repeat_frequency == 'WEEKLY' and repeat_by_weekdays:
            selected_days = [int(day) for day in repeat_by_weekdays.split(',') if day.strip()]
            
            # Find the first occurrence of each selected day
            for day_of_week in selected_days:
                # Calculate days until the next occurrence of this day
                days_ahead = day_of_week - current_date.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                    
                next_date = current_date + timedelta(days=days_ahead)
                
                # Generate events for this day
                while next_date <= (recurrence_end or datetime.now() + timedelta(days=365)):
                    if recurrence_end and next_date > recurrence_end:
                        break
                        
                    # Create event for this date
                    event_start = next_date
                    event_end = event_start + event_duration
                    
                    events_to_create.append({
                        'start': event_start.isoformat(),
                        'end': event_end.isoformat(),
                        'title': post_data.get('name', ''),
                        'location': post_data.get('location', ''),
                        'description': post_data.get('description', ''),
                        'type': post_data.get('type', 'Primary'),
                        'mandatory_invites': post_data.getlist('mandatory_invites'),
                        'optional_invites': post_data.getlist('optional_invites'),
                    })
                    
                    # Move to next occurrence (weekly)
                    next_date += timedelta(weeks=repeat_interval)
                    
        # For daily recurrence
        elif repeat_frequency == 'DAILY':
            next_date = current_date + timedelta(days=repeat_interval)
            
            while next_date <= (recurrence_end or datetime.now() + timedelta(days=365)):
                if recurrence_end and next_date > recurrence_end:
                    break
                    
                # Create event for this date
                event_start = next_date
                event_end = event_start + event_duration
                
                events_to_create.append({
                    'start': event_start.isoformat(),
                    'end': event_end.isoformat(),
                    'title': post_data.get('name', ''),
                    'location': post_data.get('location', ''),
                    'description': post_data.get('description', ''),
                    'type': post_data.get('type', 'Primary'),
                    'mandatory_invites': post_data.getlist('mandatory_invites'),
                    'optional_invites': post_data.getlist('optional_invites'),
                })
                
                # Move to next occurrence
                next_date += timedelta(days=repeat_interval)
                
        # For monthly recurrence
        elif repeat_frequency == 'MONTHLY':
            next_date = current_date + timedelta(days=30 * repeat_interval)
            
            while next_date <= (recurrence_end or datetime.now() + timedelta(days=365)):
                if recurrence_end and next_date > recurrence_end:
                    break
                    
                # Create event for this date
                event_start = next_date
                event_end = event_start + event_duration
                
                events_to_create.append({
                    'start': event_start.isoformat(),
                    'end': event_end.isoformat(),
                    'title': post_data.get('name', ''),
                    'location': post_data.get('location', ''),
                    'description': post_data.get('description', ''),
                    'type': post_data.get('type', 'Primary'),
                    'mandatory_invites': post_data.getlist('mandatory_invites'),
                    'optional_invites': post_data.getlist('optional_invites'),
                })
                
                # Move to next occurrence (approximate monthly)
                next_date += timedelta(days=30 * repeat_interval)
        
        # Store the events to create in the post_data
        post_data['recurring_events'] = events_to_create
        
    except (ValueError, KeyError, TypeError) as e:
        print("Error parsing repeat settings:", e)

    return post_data
    

@login_required
def apps_calendar_view_delete(request):
    if not request.user.has_perm("calendar_event.delete_calendarevents"):
        raise PermissionDenied

    if request.POST:
        eventid = request.POST.get('delete-event-id')
        
        # Handle prefixed event IDs (e.g., "event_11" -> "11")
        if eventid and eventid.startswith('event_'):
            eventid = eventid.replace('event_', '')

        event = get_object_or_404(CalendarEvents, pk=eventid)
        if not user_can_manage_calendar_event(request.user, event):
            raise PermissionDenied

        event.delete()
    return redirect("calendar_event:calendar-events")


@login_required
def apps_calendar_view(request):
    if not request.user.has_perm("calendar_event.view_calendarevents"):
        raise PermissionDenied

    # Get events where user is creator OR attendee (mandatory, optional, or guest)
    events = CalendarEvents.objects.filter(
        Q(creator=request.user) |
        Q(mandatory_invites=request.user) |
        Q(optional_invites=request.user) |
        Q(guests=request.user)
    ).distinct()
    
    from apps.models import TicketList
    tickets = get_visible_tickets_queryset(
        request.user, TicketList.objects.filter(due_date__isnull=False)
    ).distinct()
    
    print(f"DEBUG: Found {tickets.count()} tickets with due dates")
    for ticket in tickets[:3]:  # Show first 3 for debugging
        print(f"  - Ticket {ticket.identifier}: {ticket.name} (Due: {ticket.due_date}, Type: {type(ticket.due_date)})")
        if ticket.due_date:
            print(f"    Raw due_date: {ticket.due_date}")
            print(f"    ISO format: {ticket.due_date.isoformat()}")
            print(f"    String format: {str(ticket.due_date)}")
    
    from apps.models import ProjectList
    projects = get_visible_projects_queryset(
        request.user, ProjectList.objects.filter(due_date__isnull=False)
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
        event['className'] = 'event-type-event'
        
        # Determine if this is an all-day event based on start/end times
        start_time = event.get('start')
        end_time = event.get('end')
        
        # Check if start and end times have time components (not just dates)
        is_all_day = True
        if start_time and end_time:
            try:
                # Parse the datetime strings to check if they have time components
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                
                # If start time is not midnight (00:00:00) or end time is not midnight, it's not all-day
                if (start_dt.hour != 0 or start_dt.minute != 0 or start_dt.second != 0 or 
                    end_dt.hour != 0 or end_dt.minute != 0 or end_dt.second != 0):
                    is_all_day = False
            except:
                # If parsing fails, assume it's all-day
                is_all_day = True
        
        event['allDay'] = is_all_day
        
        # Ensure extendedProps exists for events
        if 'extendedProps' not in event:
            event['extendedProps'] = {}
        event['extendedProps']['event_type'] = 'event'
        event['extendedProps']['model'] = 'event'
        event['extendedProps']['model_id'] = event['id'].replace('event_', '')
    
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
            'allDay': True,  # Tickets are date-only (all-day events)
            'create_date': ticket.create_date.isoformat() if ticket.create_date else None,
            'project': ticket.project.name if ticket.project else None,
            'mandatory_invites': [{'user_id': tech.auth_user.user_id, 'username': tech.auth_user.username, 'email': tech.auth_user.email} for tech in ticket.assignment.all()],
            'optional_invites': [],
            'event_type': 'ticket',
            'className': 'event-type-ticket',
            'extendedProps': {
                'event_type': 'ticket',
                'model': 'ticket',
                'model_id': ticket.identifier,
                'status': ticket.status,
                'priority': ticket.priority,
                'description': ticket.description,
                'create_date': ticket.create_date.isoformat() if ticket.create_date else None,
                'project': ticket.project.name if ticket.project else None,
                'mandatory_invites': [{'user_id': tech.auth_user.user_id, 'username': tech.auth_user.username, 'email': tech.auth_user.email} for tech in ticket.assignment.all()],
                'optional_invites': []
            }
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
            'allDay': True,  # Projects are date-only (all-day events)
            'create_date': project.create_date.isoformat() if project.create_date else None,
            'mandatory_invites': [{'user_id': tech.auth_user.user_id, 'username': tech.auth_user.username, 'email': tech.auth_user.email} for tech in project.assignment.all()],
            'optional_invites': [],
            'event_type': 'project',
            'className': 'event-type-project',
            'extendedProps': {
                'event_type': 'project',
                'model': 'project',
                'model_id': project.identifier,
                'status': project.status,
                'priority': project.priority,
                'description': project.description,
                'create_date': project.create_date.isoformat() if project.create_date else None,
                'mandatory_invites': [{'user_id': tech.auth_user.user_id, 'username': tech.auth_user.username, 'email': tech.auth_user.email} for tech in project.assignment.all()],
                'optional_invites': []
            }
        }
        events_data.append(project_data)
    
    print(f"DEBUG: Found {len(events_data)} total items to display (events: {len(events)}, tickets: {tickets.count()}, projects: {projects.count()})")
    for item in events_data[:3]:  # Show first 3 for debugging
        print(f"  - {item.get('title', 'No title')} ({item.get('event_type', 'unknown')}) on {item.get('start', 'No start')}")

    if request.method == 'POST':
        # Preprocess the POST data to remove empty 'guests' field values
        clean_form = request.POST.copy()
        clean_form['creator'] = str(request.user.pk)
        eventid = clean_form.get('eventid')

        print(clean_form)
        print("\n\n")
        #? Clean Submitted form, calculation and more
        clean_form = handle_calendar_event(clean_form)
        
        # Handle recurring events
        clean_form = handle_repeated_events(clean_form)

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
        # Handle prefixed event IDs (e.g., "event_11" -> "11")
        if eventid:
            if eventid.startswith('event_'):
                eventid = eventid.replace('event_', '')
            elif eventid.startswith('ticket_'):
                # Tickets are not calendar events, so we can't update them here
                print(f"Warning: Attempted to update ticket {eventid} as calendar event")
                return redirect("calendar_event:calendar-events")
            elif eventid.startswith('project_'):
                # Projects are not calendar events, so we can't update them here
                print(f"Warning: Attempted to update project {eventid} as calendar event")
                return redirect("calendar_event:calendar-events")

        instance = get_object_or_404(CalendarEvents, pk=eventid) if eventid else None
        if instance:
            if not request.user.has_perm("calendar_event.change_calendarevents"):
                raise PermissionDenied
            if not user_can_manage_calendar_event(request.user, instance):
                raise PermissionDenied
        elif not request.user.has_perm("calendar_event.add_calendarevents"):
            raise PermissionDenied

        creator_pk = request.user.pk
        if instance and instance.creator_id:
            creator_pk = instance.creator_id
        clean_form['creator'] = str(creator_pk)

        if instance:
            if not clean_form.get('start'): 
                clean_form['start'] = instance.start
            if not clean_form.get('end'): 
                clean_form['end'] = instance.end
        form = CalendarEventForm(clean_form, instance=instance)

        if form.is_valid():
            instance = form.save(commit=False)
            if not instance.creator_id:
                instance.creator = request.user
            instance.save()
            
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
            
            # Create recurring events if they exist
            recurring_events = clean_form.get('recurring_events', [])
            if recurring_events:
                print(f"Creating {len(recurring_events)} recurring events...")
                for event_data in recurring_events:
                    # Create a new event for each recurring occurrence
                    recurring_event = CalendarEvents.objects.create(
                        name=event_data['title'],
                        start=event_data['start'],
                        end=event_data['end'],
                        location=event_data.get('location', ''),
                        description=event_data.get('description', ''),
                        type=event_data.get('type', 'Primary'),
                        creator=request.user
                    )
                    
                    # Set the same attendees for recurring events
                    if mandatory_invites_data:
                        users = []
                        for tech_id in mandatory_invites_data:
                            try:
                                tech = TechnicianUser.objects.get(pk=tech_id)
                                users.append(tech.auth_user)
                            except TechnicianUser.DoesNotExist:
                                pass
                        recurring_event.mandatory_invites.set(users)
                    
                    if optional_invites_data:
                        users = []
                        for tech_id in optional_invites_data:
                            try:
                                tech = TechnicianUser.objects.get(pk=tech_id)
                                users.append(tech.auth_user)
                            except TechnicianUser.DoesNotExist:
                                pass
                        recurring_event.optional_invites.set(users)
                    
                    if guests_data:
                        recurring_event.guests.set(guests_data)
                    
                    print(f"Created recurring event: {recurring_event.name} on {recurring_event.start}")
                
                print(f"Successfully created {len(recurring_events)} recurring events")
            
            return redirect("calendar_event:calendar-events")
        else:
            print(form.errors)

    return render(request, "apps/apps-calendar.html", context={'events': events_data, 'technicians': technicians_data})

@login_required
def apps_calendar_edit_view(request, pk):
    if not request.user.has_perm("calendar_event.view_calendarevents"):
        raise PermissionDenied

    event = get_object_or_404(CalendarEvents, pk=pk)
    if not user_can_manage_calendar_event(request.user, event):
        raise PermissionDenied

    return redirect("calendar_event:calendar-events")


class CalendarEventViewSet(viewsets.ModelViewSet):
    queryset = CalendarEvents.objects.all()
    serializer_class = CalendarEventSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated or not self.request.user.has_perm(
            "calendar_event.view_calendarevents"
        ):
            return CalendarEvents.objects.none()

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
