from django.db.models import *
from django.db.models.functions import *
from django.db.models import Prefetch
from django.shortcuts import redirect, render, reverse
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from apps.models import (
    TicketComment,
    TechnicianLabor,
    TicketFiles,
)
from apps.forms import *
from django.contrib import messages
from datetime import date
from rbac.decorators import has_permission
from rbac.utils import paginate_queryset
from django.core.exceptions import PermissionDenied
import json
import os
from django.conf import settings


#########
# TICKETS
def apps_tickets_comments_delete_view(request, ticket_pk, pk):
    tickets = TicketList.objects.get(pk=ticket_pk)
    comment = TicketComment.objects.get(pk=pk)
    comment.delete()
    return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))


def apps_tickets_comments_toggle_visibility_view(request, ticket_pk, pk):
    """Toggle comment visibility between public and private"""
    tickets = TicketList.objects.get(pk=ticket_pk)
    comment = TicketComment.objects.get(pk=pk)
    
    # Toggle the private field
    comment.private = not comment.private
    comment.save()
    
    # Set appropriate message
    if comment.private:
        messages.success(request, "Comment marked as private - hidden from clients!")
    else:
        messages.success(request, "Comment marked as public - visible to all users!")
    
    return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))


def apps_tickets_replies_toggle_visibility_view(request, ticket_pk, pk):
    """Toggle reply visibility between public and private"""
    tickets = TicketList.objects.get(pk=ticket_pk)
    reply = TicketCommentReplies.objects.get(pk=pk)
    
    # Toggle the private field
    reply.private = not reply.private
    reply.save()
    
    # Set appropriate message
    if reply.private:
        messages.success(request, "Reply marked as private - hidden from clients!")
    else:
        messages.success(request, "Reply marked as public - visible to all users!")
    
    return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))


def apps_tickets_comments_view(request, pk):
    tickets = TicketList.objects.get(pk=pk)
    
    # Get all comments ordered by oldest first
    all_comments = TicketComment.objects.filter(ticket_id=tickets).order_by('date_added')
    
    # Filter comments based on user role
    # If user is a client, only show public comments
    if request.user.groups.filter(name='Client').exists():
        comments = all_comments.filter(private=False)
    else:
        # Non-client users can see all comments
        comments = all_comments

    context = {"tickets": tickets, "comments": comments}

    if request.method == "POST":
        form = TicketCommentAddForm(request.POST or None, request.FILES or None)

        if form.is_valid():
            print(form.cleaned_data)
            form.save()
            messages.success(request, "Comment inserted Successfully!")
            if "details" in request.path:
                return redirect(
                    reverse("apps:tickets.details", kwargs={"pk": tickets.pk})
                )

            else:
                return redirect(
                    reverse("apps:tickets.details", kwargs={"pk": tickets.pk})
                )
        else:
            print(form.errors)
            print(form.cleaned_data)
            messages.error(request, "Something went wrong!")
            return redirect("apps:tickets.list")
            # return redirect(reverse("apps:tickets.list", kwargs={'pk':tickets.pk}))
    return render(request, "apps/support-tickets/apps-tickets-details.html", context)


def apps_tickets_replies_view(request, pk):
    tickets = TicketList.objects.get(pk=pk)
    
    # Get all comments and replies ordered by oldest first
    all_comments = TicketComment.objects.filter(ticket_id=tickets).order_by('date_added')
    all_replies = TicketCommentReplies.objects.filter(ticket_id=tickets).order_by('date_added')
    
    # Filter comments and replies based on user role
    # If user is a client, only show public comments and replies
    if request.user.groups.filter(name='Client').exists():
        comments = all_comments.filter(private=False)
        replies = all_replies.filter(private=False)
    else:
        # Non-client users can see all comments and replies
        comments = all_comments
        replies = all_replies
    
    context = {"tickets": tickets, "comments": comments, "replies": replies}

    if request.method == "POST":
        form = TicketRepliesAddForm(request.POST or None, request.FILES or None)

        if form.is_valid():
            form.save()
            messages.success(request, "Reply inserted Successfully!")
            # return redirect("apps:tickets.list")
            return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))
        else:
            print(form.errors)
            messages.error(request, "Something went wrong!")
            return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))
            # return redirect(reverse("apps:tickets.list", kwargs={'pk':tickets.pk}))
    return render(request, "apps/support-tickets/apps-tickets-details.html", context)


def apps_tickets_details_view(request, pk):
    tickets = TicketList.objects.get(pk=pk)
    ticket_files = TicketFiles.objects.filter(ticket_id=pk)
    projects = ProjectList.objects.filter(pk=tickets.project_id)
    
    # Get all comments ordered by oldest first
    all_comments = TicketComment.objects.filter(ticket_id=tickets).order_by('date_added')
    
    # Filter comments based on user role
    # If user is a client, only show public comments
    if request.user.groups.filter(name='Client').exists():
        comments = all_comments.filter(private=False)
    else:
        # Non-client users can see all comments
        comments = all_comments
    
    technicians = TechnicianUser.objects.all()
    replies = TicketCommentReplies.objects.filter(ticket_id=tickets)
    context = {
        "tickets": tickets,
        "comments": comments,
        "projects": projects,
        "replies": replies,
        "technicians": technicians,
        "ticket_files": ticket_files,
        "today": date.today(),
    }

    if request.method == "POST":
        form = TicketListAddForm(
            request.POST or None, request.FILES or None, instance=tickets
        )
        if form.is_valid():
            print(comments)
            form.save()
            messages.success(request, "Ticket Updates Successfully!")
            # return redirect("apps:tickets.list")
            return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))
        else:
            print(form.errors)
            messages.error(request, "Something went wrong!")
            return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))
            # return redirect(reverse("apps:tickets.list", kwargs={'pk':tickets.pk}))
    return render(request, "apps/support-tickets/apps-tickets-details.html", context)


def get_ticket_list_data(request, per_page=8):
    all_tickets = (
        TicketList.objects.select_related("client")
        .prefetch_related(
            Prefetch(
                "assignment",
                queryset=TechnicianUser.objects.select_related("auth_user"),
            )
        )
        .all()
        .order_by("pk")
    )

    user = request.user
    if hasattr(user, "client"):
        # A client is logged in
        all_tickets = all_tickets.filter(client__users=user.client)

    open_tickets = all_tickets.exclude(status__in=["Closed", "Completed"])
    closed_tickets = all_tickets.filter(status="Closed")
    completed_tickets = all_tickets.filter(status="Completed")

    all_page_number = request.GET.get("all_page", 1)
    open_page_number = request.GET.get("open_page", 1)
    closed_page_number = request.GET.get("closed_page", 1)
    completed_page_number = request.GET.get("completed_page", 1)

    all_tickets_paginated, allTicketsPaginator = paginate_queryset(
        all_tickets, all_page_number, per_page
    )
    completed_tickets_paginated, completedTicketsPaginator = paginate_queryset(
        completed_tickets, completed_page_number, per_page
    )
    open_tickets_paginated, openTicketsPaginator = paginate_queryset(
        open_tickets, open_page_number, per_page
    )
    closed_tickets_paginated, closedTicketsPaginator = paginate_queryset(
        closed_tickets, closed_page_number, per_page
    )

    query_params_pagination_type = (
        request.GET.get("closed_page")
        or request.GET.get("open_page")
        or request.GET.get("completed_page")
    )

    active_tab = "open"
    if query_params_pagination_type:
        if "closed_page" in request.GET:
            active_tab = "closed"
        elif "completed_page" in request.GET:
            active_tab = "completed"

    return {
        "total_tickets": all_tickets.count(),
        "all_tickets": all_tickets_paginated,
        "completed_tickets": completed_tickets_paginated,
        "open_tickets": open_tickets_paginated,
        "closed_tickets": closed_tickets_paginated,
        "all_tickets_is_paginated": all_tickets_paginated.has_other_pages(),
        "open_tickets_is_paginated": open_tickets_paginated.has_other_pages(),
        "closed_tickets_is_paginated": closed_tickets_paginated.has_other_pages(),
        "completed_tickets_is_paginated": completed_tickets_paginated.has_other_pages(),
        "allPaginator": allTicketsPaginator,
        "openPaginator": openTicketsPaginator,
        "closedPaginator": closedTicketsPaginator,
        "completedPaginator": completedTicketsPaginator,
        "active_tab": active_tab,
    }


def get_ticket_stats_data():
    ticket_stats = TicketList.objects.aggregate(
        total_count=Count("pk"),
        open_count=Count("pk", filter=~Q(status="Closed")),
        closed_count=Count("pk", filter=Q(status="Closed")),
        completed_count=Count("pk", filter=Q(status="Completed")),
    )

    return {
        "total_tickets": ticket_stats["total_count"],
        "open_tickets_count": ticket_stats["open_count"],
        "closed_tickets_count": ticket_stats["closed_count"],
        "completed_tickets_count": ticket_stats["completed_count"],
    }


def get_labor_stats_data():
    labor_stats = TechnicianLabor.objects.aggregate(total_minutes=Sum("minutes"))
    total_minutes = labor_stats["total_minutes"] or 0

    return {
        "labor_hours": total_minutes // 60,
        "labor_minutes": total_minutes % 60,
    }


def get_estimated_work_data(context: dict):
    estimated_work = (
        TicketList.objects.exclude(status="Closed")
        .annotate(
            days_until=ExpressionWrapper(
                F("due_date") - Now(), output_field=DateField()
            )
        )
        .annotate(
            days_until_int=Cast(F("days_until__day"), output_field=IntegerField())
        )
        .aggregate(
            total_days=Sum(
                Case(
                    When(due_date__gt=Now(), then=F("days_until_int")),
                    default=0,
                    output_field=IntegerField(),
                )
            )
        )
    )

    return {
        "estimated_work": estimated_work["total_days"] or 0,
    }


def get_technician_data():
    technicians = TechnicianUser.objects.all()
    return {
        "technicians": technicians,
    }


def get_client_data():
    clients = ClientCompany.objects.all().order_by("-name")
    return {
        "clients": clients,
    }


@has_permission("apps.view_ticketlist", "apps.view_own_ticketlist", condition="OR")
def apps_tickets_list_view(request):
    context = {}
    context.update(get_ticket_list_data(request))

    # Group work types by client
    work_types_by_client = {}
    for work_type in ClientWorkTypeRate.objects.all():
        if work_type.client_id not in work_types_by_client:
            work_types_by_client[work_type.client_id] = []
        work_types_by_client[work_type.client_id].append(
            {
                "id": work_type.id,
                "name": work_type.name,
                "rate": str(
                    work_type.rate
                ),  # Convert Decimal to string for JSON serialization
            }
        )

    # Convert to JSON string for template
    context["work_types_by_client"] = json.dumps(work_types_by_client)

    if request.user.has_perm("apps.view_ticket_stats"):
        context.update(get_ticket_stats_data())

    if request.user.has_perm("apps.view_labor_stats"):
        context.update(get_labor_stats_data())

    if request.user.has_perm("apps.view_estimated_work"):
        context.update(get_estimated_work_data(context))

    if request.user.has_perm("apps.view_technicians"):
        context.update(get_technician_data())

    if request.user.has_perm("apps.view_clientcompany"):
        context.update(get_client_data())

    return render(request, "apps/support-tickets/apps-tickets-list.html", context)


@has_permission("apps.add_ticketlist")
def apps_tickets_create_view(request):
    if request.method == "POST":
        form = TicketListAddForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save()
            for file in request.FILES.getlist("files"):
                if file:
                    file.name = file.name[:100]  # Truncate filename if necessary
                    TicketFiles.objects.create(file=file, ticket=ticket)
            messages.success(request, "Ticket Created!")
            return JsonResponse({"message": "Ticket created successfully!"}, status=201)
        else:
            messages.error(request, "Something went wrong!")
            print(form.errors)
            return JsonResponse(
                {"message": "Something went wrong!", "errors": form.errors}, status=400
            )

    return redirect("apps.tickets.list")


@has_permission("apps.close_ticketlist")
def apps_tickets_close_view(request, pk):
    ticket = TicketList.objects.get(pk=pk)
    ticket.status = "Closed"
    ticket.save()
    messages.success(request, "Tickets status set to Closed Successfully!")
    return redirect("apps:tickets.list")


@has_permission("apps.complete_ticketlist")
def apps_tickets_complete_view(request, pk):
    ticket = TicketList.objects.get(pk=pk)
    ticket.status = "Completed"
    ticket.save()
    messages.success(request, "Tickets status set to Completed Successfully!")
    return redirect("apps:tickets.list")


@has_permission("apps.change_ticketlist")
def apps_tickets_edit_view(request, pk):
    tickets = TicketList.objects.get(pk=pk)
    technicians = TechnicianUser.objects.all()
    projects = ProjectList.objects.all()
    clients = ClientCompany.objects.all()
    comments = TicketComment.objects.filter(ticket_id=tickets)
    ticket_files = TicketFiles.objects.filter(ticket_id=pk)
    files_count = ticket_files.count()
    comments_count = comments.count()
    labors = TechnicianLabor.objects.filter(ticket_id=tickets)
    work_types = ClientWorkTypeRate.objects.filter(client_id=tickets.client_id)
    labors_count = labors.count()
    work_types_by_client = {}
    # Group work types by client, and format for json
    for work_type in ClientWorkTypeRate.objects.all():
        if work_type.client_id not in work_types_by_client:
            work_types_by_client[work_type.client_id] = []
        work_types_by_client[work_type.client_id].append(
            {
                "id": work_type.id,
                "name": work_type.name,
                "rate": str(work_type.rate),
            }
        )

    tags = ", ".join([x for x in tickets.tag.all().values_list("name", flat=True)])

    if labors.count() == 0:
        labor_hours = 0
        labor_minutes = 0
    else:
        labor_hours = labors.aggregate(Sum("minutes"))["minutes__sum"] // 60
        labor_minutes = labors.aggregate(Sum("minutes"))["minutes__sum"] % 60

    context = {
        "tickets": tickets,
        "projects": projects,
        "technicians": technicians,
        "comments": comments,
        "comments_count": comments_count,
        "clients": clients,
        "labors": labors,
        "labors_count": labors_count,
        "labor_hours": labor_hours,
        "labor_minutes": labor_minutes,
        "tags": tags,
        "ticket_files": ticket_files,
        "files_count": files_count,
        "work_types": work_types,
        "work_types_by_client": json.dumps(work_types_by_client),
    }

    if request.method == "POST":
        form = TicketListAddForm(
            request.POST or None, request.FILES or None, instance=tickets
        )

        if form.is_valid():
            ticket = form.save()

            files = request.FILES.getlist("files")
            for file in files:
                if file:
                    # Truncate the file name to 100 characters if necessary
                    file.name = file.name[:100]
                    ticketFile = TicketFiles(file=file, ticket=ticket)
                    ticketFile.save()
                    print("Saved File ID:", ticketFile.id)

            messages.success(request, "Tickets updated Successfully!")
            
            # Redirect to project overview if ticket has a project, otherwise to ticket list
            if ticket.project:
                return redirect("apps:projects.overview", pk=ticket.project.pk)
            else:
                return redirect("apps:tickets.list")

        else:
            print(form.errors)
            print(f"Files: {request.FILES}")
            messages.error(request, "Something went wrong!")
            return JsonResponse(
                {"message": "Something went wrong!", "error": str(form.errors)},
                status=400,
            )

    return render(request, "apps/support-tickets/apps-tickets-update.html", context)


@has_permission("apps.delete_ticketlist")
def apps_tickets_delete_list_view(request, pk):
    tickets = TicketList.objects.get(pk=pk)
    tickets.delete()
    messages.success(request, "Tickets deleted Successfully!")
    return redirect("apps:tickets.list")


def apps_ticket_download_file(request, pk):
    file_obj = get_object_or_404(TicketFiles, pk=pk)
    response = FileResponse(file_obj.file, as_attachment=True)
    return response


@has_permission("apps.change_ticketlist")
def apps_ticket_file_rename_view(request, pk):
    """Rename a ticket file"""
    if request.method == "POST":
        file_obj = get_object_or_404(TicketFiles, pk=pk)
        new_name = request.POST.get('new_name', '').strip()
        
        if not new_name:
            return JsonResponse({'success': False, 'message': 'New name is required'})
        
        try:
            # Get the file extension
            old_path = file_obj.file.path
            file_extension = os.path.splitext(old_path)[1]
            
            # Create new filename with extension
            new_filename = new_name + file_extension
            
            # Create new path
            new_path = os.path.join(os.path.dirname(old_path), new_filename)
            
            # Rename the file on disk
            os.rename(old_path, new_path)
            
            # Update the file field in the database
            file_obj.file.name = os.path.relpath(new_path, settings.MEDIA_ROOT)
            file_obj.save()
            
            return JsonResponse({
                'success': True, 
                'message': 'File renamed successfully',
                'new_filename': new_filename
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error renaming file: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@has_permission("apps.delete_ticketlist")
def apps_ticket_file_delete_view(request, pk):
    """Delete a ticket file"""
    if request.method == "POST":
        file_obj = get_object_or_404(TicketFiles, pk=pk)
        
        try:
            # Get the ticket ID for redirect
            ticket_id = file_obj.ticket.pk
            
            # Delete the file from disk
            if file_obj.file and os.path.exists(file_obj.file.path):
                os.remove(file_obj.file.path)
            
            # Delete the database record
            file_obj.delete()
            
            messages.success(request, "File deleted successfully!")
            return redirect(reverse("apps:tickets.details", kwargs={"pk": ticket_id}))
            
        except Exception as e:
            messages.error(request, f"Error deleting file: {str(e)}")
            return redirect(reverse("apps:tickets.details", kwargs={"pk": file_obj.ticket.pk}))
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
