# Import Python
import json
from datetime import datetime, timezone
from django.utils import timezone as django_timezone

# Import Django

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

# Import Models

from .models import TicketList, TechnicianLabor

# API View

def api_start_timer(request,pk):
    ticket = TicketList.objects.get(pk=pk)
    print(request.user)
    print(django_timezone.now())
    if not hasattr(request.user, 'technician'):
        return JsonResponse({'success': False})
        
    technician =  request.user.technician
    entry = TechnicianLabor.objects.create(
        ticket_id=ticket.pk,
        minutes=0,
        created_by=technician,
        is_tracked=False,
        created_at=django_timezone.now()
    )

    print(entry)

    return JsonResponse({'success': True})

def api_stop_timer(request, pk):
    if not hasattr(request.user, 'technician'):
        return JsonResponse({'success': False})
        
    technician =  request.user.technician

    ticket = TicketList.objects.get(pk=pk)
    entry = TechnicianLabor.objects.get(
        ticket_id=ticket.pk,
        created_by=technician,
        minutes=0,
        is_tracked=False
    )

    tracked_minutes = int((django_timezone.now() - entry.created_at).total_seconds() / 60)

    if tracked_minutes < 1:
        tracked_minutes = 1
    
    entry.minutes = tracked_minutes
    entry.is_tracked = False
    entry.save()

    return JsonResponse({'success': True, 'entryID': entry.id})

def api_discard_timer(request):
    entries = TechnicianLabor.objects.filter(ticket_id=request.GET.get('ticket_id', ''), created_by=request.user, is_tracked=False).order_by('-created_at')

    if entries:
        entry = entries.first()
        entry.delete()
    
    return JsonResponse({'success': True})

# def api_get_tasks(request):
#     ticket_id = request.GET.get('ticket_id', '')

#     if ticket_id:
#         tasks = []
#         ticket = get_object_or_404(TicketList, pk=ticket_id)

#         for task in ticket.tasks.all():
#             obj = {
#                 'id': task.id,
#                 'title': task.title
#             }
#             tasks.append(obj)
    
#         return JsonResponse({'success': True, 'tasks': tasks})
    
#     return JsonResponse({'success': False})
