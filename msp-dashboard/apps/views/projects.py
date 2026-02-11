from django.core.exceptions import PermissionDenied
from auditlog.models import LogEntry
from django.shortcuts import redirect, render, reverse
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from apps.models import ProjectComment, ProjectFiles, PROJECT_STATUS

from apps.forms import *
from apps.utils import user_can_see_private_comments
from django.contrib import messages
from rbac.decorators import has_permission
from rbac.utils import paginate_queryset

##########
# Projects


def get_projects_data(request, per_page=10):
    user = request.user
    base_query = ProjectList.objects.select_related("client").prefetch_related(
        Prefetch(
            "assignment", queryset=TechnicianUser.objects.select_related("auth_user")
        ),
        Prefetch(
            "tickets", queryset=TicketList.objects.all()
        )
    )
    page_number = request.GET.get("active_projects_page", 1)
    archived_page_number = request.GET.get("archived_projects_page", 1)

    if hasattr(user, "client"):
        active_projects = (
            base_query.filter(client__users=user.client)
            .exclude(status="Completed")
            .order_by("-create_date")
        )
    else:
        active_projects = (
            base_query.all().exclude(status="Completed").order_by("-create_date")
        )

    # Calculate ticket counts for each project
    for project in active_projects:
        # Use the same logic as project overview - only count tickets with proper ForeignKey relationships
        project_tickets = project.tickets.filter(project=project)
        project.all_tickets_count = project_tickets.count()
        project.completed_tickets_count = project_tickets.filter(status__in=["Completed", "Closed"]).count()
        
        try:
            project.percentage = (project.completed_tickets_count / project.all_tickets_count) * 100
        except ZeroDivisionError:
            project.percentage = 0

    paginated_projects, paginator = paginate_queryset(
        active_projects, page_number, per_page
    )

    archived_projects = base_query.filter(status="Completed")
    
    # Calculate ticket counts for archived projects too
    for project in archived_projects:
        # Use the same logic as project overview - only count tickets with proper ForeignKey relationships
        project_tickets = project.tickets.filter(project=project)
        project.all_tickets_count = project_tickets.count()
        project.completed_tickets_count = project_tickets.filter(status__in=["Completed", "Closed"]).count()
        
        try:
            project.percentage = (project.completed_tickets_count / project.all_tickets_count) * 100
        except ZeroDivisionError:
            project.percentage = 0
    
    paginated_archived_projects, paginator_archived = paginate_queryset(
        archived_projects, archived_page_number, per_page
    )

    query_params_pagination_type = request.GET.get(
        "active_projects_page"
    ) or request.GET.get("archived_projects_page")

    active_tab = "active_projects"
    if query_params_pagination_type and "archived_projects_page" in request.GET:
        active_tab = "archived_projects"

    return {
        "projects": paginated_projects,
        "archived_projects": paginated_archived_projects,
        "project_count": active_projects.count(),
        "archived_project_count": archived_projects.count(),
        "active_tab": active_tab,
    }


def get_technicians_data():
    return {
        "technicians": TechnicianUser.objects.all(),
    }


def get_tickets_data(request):
    user = request.user
    if hasattr(user, "client"):
        tickets = TicketList.objects.filter(client=user.client.company)
    else:
        tickets = TicketList.objects.all()

    all_tickets_count = tickets.count()
    active_tickets_count = tickets.exclude(status="Closed").count()

    try:
        percentage = (active_tickets_count / all_tickets_count) * 100
    except ZeroDivisionError:
        percentage = 0

    return {
        "tickets": tickets,
        "all_tickets_count": all_tickets_count,
        "active_tickets_count": active_tickets_count,
        "percentage": percentage,
    }


@has_permission("apps.view_projectlist", "apps.view_own_projects", condition="OR")
def apps_projects_list_view(request):
    context = {
        "status1": ["New", "In Progress", "Scheduled"],
        "status2": ["Follow up", "Reviewing", "Observing"],
        "status3": ["Waiting on Client", "Waiting on Vendor", "Waiting on Client"],
    }

    if request.user.has_perm("apps.view_projectlist") or request.user.has_perm(
        "apps.view_own_projects"
    ):
        context.update(get_projects_data(request))
    else:
        raise PermissionDenied

    if request.user.has_perm("apps.view_technicians"):
        context.update(get_technicians_data())

    if request.user.has_perm("apps.view_ticketlist") or request.user.has_perm(
        "apps.view_own_ticketlist"
    ):
        context.update(get_tickets_data(request))

    context["is_client"] = hasattr(request.user, "client")
    context["is_admin"] = request.user.is_staff or request.user.is_superuser

    return render(request, "apps/projects/apps-projects-list.html", context)


def apps_projects_overview_view(request, pk):
    projects = ProjectList.objects.get(pk=pk)
    projects_log = LogEntry.objects.get_for_object(projects)
    technicians = TechnicianUser.objects.all()
    
    # Get tickets that have both ManyToMany and ForeignKey relationships properly set
    # Only show tickets that have their ForeignKey pointing to this project
    tickets = projects.tickets.filter(project=projects)
    
    # Get all comments and replies ordered by oldest first
    all_comments = ProjectComment.objects.filter(project_id=projects).order_by('date_added')
    all_replies = ProjectCommentReplies.objects.filter(project_id=projects).order_by('date_added')
    
    # Only IT Dept, Administrator, Super User (and superuser) see private comments/replies
    if not user_can_see_private_comments(request.user):
        comments = all_comments.filter(private=False)
        replies = all_replies.filter(private=False)
    else:
        comments = all_comments
        replies = all_replies
    
    teammembers = ClientTeamMembers.objects.filter(client_id=projects.client.pk)

    project_tickets = tickets  # Use the filtered tickets
    project_files = ProjectFiles.objects.filter(project_id=pk)
    projects_files_log = LogEntry.objects.get_for_objects(project_files)
    project_tickets_count = project_tickets.count()

    print(projects)

    context = {
        "tickets": tickets,
        "project": projects,
        "technicians": technicians,
        "teammembers": teammembers,
        "project_tickets": project_tickets,
        "project_tickets_count": project_tickets_count,
        "comments": comments,
        "replies": replies,
        "project_files": project_files,
        "projects_files_log": projects_files_log,
        "projects_log": projects_log,
    }
    return render(request, "apps/projects/apps-projects-overview.html", context)


@has_permission("apps.change_projectlist")
def apps_projects_edit_list_view(request, pk):
    projects = ProjectList.objects.get(pk=pk)
    technicians = TechnicianUser.objects.all()
    clients = ClientCompany.objects.all().order_by("-name")
    # Show all tickets (both unassigned and already assigned to this project)
    tickets = TicketList.objects.all()
    tags = ", ".join([x for x in projects.tag.all().values_list("name", flat=True)])
    if request.method == "POST":
        form = ProjectListAddForm(
            request.POST or None, request.FILES or None, instance=projects
        )

        if form.is_valid():
            project = form.save()

            # Handle tickets assignment
            tickets = form.cleaned_data.get('tickets')
            print("DEBUG: Form tickets:", tickets)
            print("DEBUG: Form tickets count:", len(tickets) if tickets else 0)
            if tickets:
                project.tickets.set(tickets)
                print("DEBUG: ManyToMany set, count:", project.tickets.count())
                # Also update the ForeignKey relationship for each ticket
                for ticket in tickets:
                    ticket.project = project
                    ticket.save()
                    print(f"DEBUG: Updated ForeignKey for ticket {ticket.name}")
                print("DEBUG: Final ManyToMany count:", project.tickets.count())
            else:
                print("DEBUG: No tickets in form, clearing all")
                # If no tickets selected, clear all existing tickets
                project.tickets.clear()
                # Also clear ForeignKey relationships for all tickets that were previously in this project
                TicketList.objects.filter(project=project).update(project=None)

            files = request.FILES.getlist("files")
            for file in files:
                if file:
                    # Truncate the file name to 100 characters if necessary
                    file.name = file.name[:100]
                    projectFile = ProjectFiles(file=file, project=project)
                    projectFile.save()
                    print("Saved File ID:", projectFile.id)

            messages.success(request, "Project Updated Successfully!")
            return JsonResponse(
                {
                    "message": "Project Updated successfully!",
                    "redirect_url": reverse("apps:projects.overview", kwargs={"pk": project.pk})
                }, status=201
            )

        else:
            print(form.errors)
            print(f"Files: {request.FILES}")
            messages.error(request, "Something went wrong!")
            return JsonResponse(
                {
                    "message": "Something went wrong!", 
                    "error": str(form.errors),
                    "redirect_url": reverse("apps:projects.edit", kwargs={"pk": projects.pk})
                },
                status=400,
            )

    return render(
        request,
        "apps/projects/apps-projects-update.html",
        context={
            "PROJECT_STATUS": PROJECT_STATUS,
            "projects": projects,
            "technicians": technicians,
            "tickets": tickets,
            "clients": clients,
            "tags": tags,
        },
    )


@has_permission("apps.add_projectlist")
def apps_projects_create_view(request):
    technicians = TechnicianUser.objects.all()
    tickets = TicketList.objects.all()
    clients = ClientCompany.objects.all().order_by("-name")

    context = {
        "technicians": technicians,
        "tickets": tickets,
        "clients": clients,
        "PROJECT_STATUS": PROJECT_STATUS,
    }

    if request.method == "POST":
        form = ProjectListAddForm(request.POST, request.FILES or None)
        print("DEBUG: POST data:", request.POST)
        print("DEBUG: Tickets in POST:", request.POST.getlist('tickets'))

        if form.is_valid():
            project = form.save()
            print("DEBUG: Project saved with ID:", project.pk)

            # Handle tickets assignment
            tickets = form.cleaned_data.get('tickets')
            print("DEBUG: Tickets from form.cleaned_data:", tickets)
            if tickets:
                project.tickets.set(tickets)
                # Also update the ForeignKey relationship for each ticket
                for ticket in tickets:
                    ticket.project = project
                    ticket.save()
                print("DEBUG: Tickets assigned to project:", project.tickets.count())
            else:
                print("DEBUG: No tickets to assign")
                # If no tickets selected, clear all existing tickets
                project.tickets.clear()
                # Also clear ForeignKey relationships for all tickets that were previously in this project
                TicketList.objects.filter(project=project).update(project=None)

            files = request.FILES.getlist("files")
            for file in files:
                if file:
                    # Truncate the file name to 100 characters if necessary
                    file.name = file.name[:100]
                    projectFile = ProjectFiles(file=file, project=project)
                    projectFile.save()
            messages.success(request, "Project created successfully!")
        else:
            print("DEBUG: Form errors:", form.errors)
            print("DEBUG: Form non-field errors:", form.non_field_errors())
            messages.error(request, "Something went wrong!")
        return redirect("apps:projects.list")

    return render(request, "apps/projects/apps-projects-create.html", context=context)


def apps_projects_delete_list_view(request, pk):
    projects = ProjectList.objects.get(pk=pk)
    projects.delete()
    messages.success(request, "Project deleted Successfully!")
    return redirect("apps:projects.list")


def apps_projects_comments_view(request, pk):
    projects = ProjectList.objects.get(pk=pk)
    context = {"projects": projects}

    if request.method == "POST":
        form = ProjectCommentAddForm(request.POST or None, request.FILES or None)

        if form.is_valid():
            print(form.cleaned_data)
            form.save()
            messages.success(request, "Comment inserted Successfully!")
            # return redirect("apps:tickets.list")
            return redirect(
                reverse("apps:projects.overview", kwargs={"pk": projects.pk})
            )
        else:
            print(form.errors)
            print(form.cleaned_data)
            print(projects.pk)
            messages.error(request, "Something went wrong!")
            return redirect("apps:projects.list")
            # return redirect(reverse("apps:tickets.list", kwargs={'pk':tickets.pk}))
    return redirect("apps:project.overview", context)


def apps_projects_replies_view(request, pk):
    projects = ProjectList.objects.get(pk=pk)
    
    # Get all comments and replies ordered by oldest first
    all_comments = ProjectComment.objects.filter(project_id=projects).order_by('date_added')
    all_replies = ProjectCommentReplies.objects.filter(project_id=projects).order_by('date_added')
    
    # Only IT Dept, Administrator, Super User (and superuser) see private comments/replies
    if not user_can_see_private_comments(request.user):
        comments = all_comments.filter(private=False)
        replies = all_replies.filter(private=False)
    else:
        comments = all_comments
        replies = all_replies
    
    context = {"project": projects, "comments": comments, "replies": replies}

    if request.method == "POST":
        form = ProjectRepliesAddForm(request.POST or None, request.FILES or None)

        if form.is_valid():
            form.save()
            messages.success(request, "Reply inserted Successfully!")
            # return redirect("apps:tickets.list")
            return redirect(
                reverse("apps:projects.overview", kwargs={"pk": projects.pk})
            )
        else:
            print(form.errors)
            messages.error(request, "Something went wrong!")
            return redirect(
                reverse("apps:projects.overview", kwargs={"pk": projects.pk})
            )
            # return redirect(reverse("apps:tickets.list", kwargs={'pk':tickets.pk}))
    return render(request, "apps/projects/apps-projects-overview.html", context)


def apps_projects_remove_ticket_view(request, pk):
    ticket = TicketList.objects.get(pk=pk)
    # Find the project that contains this ticket
    project = ProjectList.objects.filter(tickets=ticket).first()
    
    if project:
        # Remove from ManyToManyField relationship
        project.tickets.remove(ticket)
        # Also clear the ForeignKey relationship
        ticket.project = None
        ticket.save()
        
        messages.success(request, "Ticket Removed Successfully!")
        return redirect(reverse("apps:projects.overview", kwargs={"pk": project.pk}))
    else:
        messages.error(request, "Ticket not found in any project!")
        return redirect("apps:projects.list")


def apps_projects_download_file(request, pk):
    project_file = get_object_or_404(ProjectFiles, pk=pk)
    file_path = project_file.file.path
    response = FileResponse(open(file_path, "rb"))
    response["Content-Type"] = "application/octet-stream"
    response["Content-Disposition"] = f'attachment; filename="{project_file.file.name}"'
    return response


def apps_projects_remove_tech_view(request, project_pk, tech_pk):
    project = ProjectList.objects.get(pk=project_pk)
    technician = TechnicianUser.objects.get(pk=tech_pk)
    technician.projectlist_set.remove(project)
    messages.success(request, "Technician Removed from Project Successfully!")
    return redirect("apps:projects.list")


def apps_projects_comments_toggle_visibility_view(request, project_pk, pk):
    projects = ProjectList.objects.get(pk=project_pk)
    comment = ProjectComment.objects.get(pk=pk)
    comment.private = not comment.private
    comment.save()
    if comment.private:
        messages.success(request, "Comment marked as private - hidden from clients!")
    else:
        messages.success(request, "Comment marked as public - visible to all users!")
    return redirect(reverse("apps:projects.overview", kwargs={"pk": projects.pk}))


def apps_projects_replies_toggle_visibility_view(request, project_pk, pk):
    projects = ProjectList.objects.get(pk=project_pk)
    reply = ProjectCommentReplies.objects.get(pk=pk)
    reply.private = not reply.private
    reply.save()
    if reply.private:
        messages.success(request, "Reply marked as private - hidden from clients!")
    else:
        messages.success(request, "Reply marked as public - visible to all users!")
    return redirect(reverse("apps:projects.overview", kwargs={"pk": projects.pk}))
