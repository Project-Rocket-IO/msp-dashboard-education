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
    TicketList,
    ClientCompany,
)
from accounts.models import TechnicianUser
from apps.forms import *
from django.contrib import messages
from datetime import date, datetime
from rbac.decorators import has_permission
from rbac.utils import paginate_queryset
from django.core.exceptions import PermissionDenied
import json
import os
import tempfile
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

# Try to import pandas for Excel processing
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


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

    open_tickets = all_tickets.exclude(status__in=["Closed"])
    closed_tickets = all_tickets.filter(status="Closed")

    all_page_number = request.GET.get("all_page", 1)
    open_page_number = request.GET.get("open_page", 1)
    closed_page_number = request.GET.get("closed_page", 1)

    all_tickets_paginated, allTicketsPaginator = paginate_queryset(
        all_tickets, all_page_number, per_page
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
    )

    active_tab = "open"
    if query_params_pagination_type:
        if "closed_page" in request.GET:
            active_tab = "closed"

    return {
        "total_tickets": all_tickets.count(),
        "all_tickets": all_tickets_paginated,
        "open_tickets": open_tickets_paginated,
        "closed_tickets": closed_tickets_paginated,
        "all_tickets_is_paginated": all_tickets_paginated.has_other_pages(),
        "open_tickets_is_paginated": open_tickets_paginated.has_other_pages(),
        "closed_tickets_is_paginated": closed_tickets_paginated.has_other_pages(),
        "allPaginator": allTicketsPaginator,
        "openPaginator": openTicketsPaginator,
        "closedPaginator": closedTicketsPaginator,
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
            return redirect("apps:tickets.list")
        else:
            messages.error(request, "Something went wrong!")
            print(form.errors)
            return redirect("apps:tickets.list")

    return redirect("apps:tickets.list")


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
    labors_count = labors.count()

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


@has_permission("apps.add_ticketlist")
def apps_tickets_bulk_upload_view(request):
    """Handle bulk ticket creation from Excel file"""
    if not PANDAS_AVAILABLE:
        return JsonResponse({
            "success": False,
            "message": "Excel processing is not available. Please contact your administrator."
        }, status=500)
    
    if request.method == "POST":
        try:
            if 'excel_file' not in request.FILES:
                return JsonResponse({"success": False, "message": "No file was uploaded."}, status=400)
            
            uploaded_file = request.FILES['excel_file']
            
            if uploaded_file.size > 262144000: # 250MB
                return JsonResponse({"success": False, "message": "File size exceeds 250MB limit."}, status=400)
            
            if not uploaded_file.name.endswith(('.xlsx', '.xls')):
                return JsonResponse({"success": False, "message": "Please upload an Excel file (.xlsx or .xls)."}, status=400)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                df = pd.read_excel(temp_file_path)
                
                # Updated required columns
                required_columns = ['name', 'client', 'technician']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    return JsonResponse({"success": False, "message": f"Missing required columns: {', '.join(missing_columns)}"}, status=400)
                
                created_count = 0
                errors = []
                
                for index, row in df.iterrows():
                    try:
                        # Handle required fields
                        ticket_name = str(row['name']).strip()
                        if not ticket_name:
                            errors.append(f"Row {index + 2}: Ticket name cannot be empty")
                            continue
                        
                        client_name = str(row['client']).strip()
                        if not client_name:
                            errors.append(f"Row {index + 2}: Client name cannot be empty")
                            continue
                        
                        technician_name = str(row['technician']).strip()
                        if not technician_name:
                            errors.append(f"Row {index + 2}: Technician name cannot be empty")
                            continue
                        
                        # Create or get client
                        client, created = ClientCompany.objects.get_or_create(
                            name=client_name,
                            defaults={'email': f'{client_name.lower().replace(" ", "")}@example.com'}
                        )
                        
                        # Find technician by username
                        try:
                            technician = TechnicianUser.objects.get(auth_user__username=technician_name)
                        except TechnicianUser.DoesNotExist:
                            errors.append(f"Row {index + 2}: Technician '{technician_name}' not found")
                            continue
                        
                        # Create ticket with required fields
                        ticket = TicketList.objects.create(
                            name=ticket_name,
                            client=client,
                            description=str(row.get('description', '')).strip() if 'description' in df.columns and pd.notna(row.get('description')) else '',
                        )
                        
                        # Add technician assignment
                        ticket.assignment.add(technician)
                        
                        # Handle optional fields
                        if 'due_date' in df.columns and pd.notna(row['due_date']):
                            if isinstance(row['due_date'], str):
                                try:
                                    ticket.due_date = datetime.strptime(row['due_date'], '%Y-%m-%d').date()
                                except ValueError:
                                    pass
                            else:
                                ticket.due_date = row['due_date'].date()
                        
                        if 'ticket_type' in df.columns and pd.notna(row['ticket_type']):
                            ticket.ticket_type = str(row['ticket_type']).strip()
                        
                        if 'status' in df.columns and pd.notna(row['status']):
                            ticket.status = str(row['status']).strip()
                        else:
                            ticket.status = 'New'  # Default status
                        
                        if 'priority' in df.columns and pd.notna(row['priority']):
                            ticket.priority = str(row['priority']).strip()
                        else:
                            ticket.priority = 'Medium'  # Default priority
                        
                        ticket.save()
                        created_count += 1
                        
                    except Exception as e:
                        errors.append(f"Row {index + 2}: {str(e)}")
                
                os.unlink(temp_file_path) # Delete file after processing
                
                if created_count > 0:
                    message = f"Successfully created {created_count} tickets."
                    if errors:
                        message += f" Errors: {len(errors)} rows failed."
                    return JsonResponse({
                        "success": True,
                        "message": message,
                        "created_count": created_count,
                        "errors": errors
                    })
                else:
                    return JsonResponse({
                        "success": False,
                        "message": "No tickets were created. Please check your Excel file format."
                    }, status=400)
                        
            except Exception as e:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                return JsonResponse({
                    "success": False,
                    "message": f"Error processing Excel file: {str(e)}"
                }, status=400)
                    
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }, status=500)
    
    return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)
