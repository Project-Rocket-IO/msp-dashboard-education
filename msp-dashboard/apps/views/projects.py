from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from auditlog.models import LogEntry
from django.shortcuts import redirect, render, reverse
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from apps.models import (
    ClientCompany,
    ClientTeamMembers,
    ProjectComment,
    ProjectCommentReplies,
    ProjectFiles,
    ProjectList,
    PROJECT_STATUS,
    TechnicianUser,
    TicketList,
)

from apps.access import (
    get_visible_projects_queryset,
    get_visible_tickets_queryset,
    user_can_access_project,
    user_can_see_private_comments,
)
from apps.forms import ProjectCommentAddForm, ProjectListAddForm, ProjectRepliesAddForm
from django.contrib import messages
from rbac.decorators import has_permission
from rbac.utils import paginate_queryset

##########
# Projects
def _get_project_or_404_for_user(request, pk):
    return get_object_or_404(get_visible_projects_queryset(request.user), pk=pk)


def _get_project_comments_queryset(project, user):
    comments = ProjectComment.objects.filter(project=project).order_by("date_added")
    if user_can_see_private_comments(user):
        return comments
    return comments.filter(private=False)


def _get_project_replies_queryset(project, user):
    replies = ProjectCommentReplies.objects.filter(project=project).order_by("date_added")
    if user_can_see_private_comments(user):
        return replies
    return replies.filter(private=False)


def get_projects_data(request, per_page=10):
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
    visible_projects = get_visible_projects_queryset(request.user, base_query)
    active_projects = visible_projects.exclude(status="Completed").order_by("-create_date")

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

    archived_projects = visible_projects.filter(status="Completed")
    
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
    tickets = get_visible_tickets_queryset(request.user)

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
    projects = _get_project_or_404_for_user(request, pk)
    projects_log = LogEntry.objects.get_for_object(projects)
    technicians = TechnicianUser.objects.all()
    
    tickets = get_visible_tickets_queryset(
        request.user, projects.tickets.filter(project=projects)
    )
    comments = _get_project_comments_queryset(projects, request.user)
    replies = _get_project_replies_queryset(projects, request.user)
    
    teammembers = ClientTeamMembers.objects.filter(client_id=projects.client.pk)

    project_tickets = tickets  # Use the filtered tickets
    project_files = ProjectFiles.objects.filter(project_id=pk)
    projects_files_log = LogEntry.objects.get_for_objects(project_files)
    project_tickets_count = project_tickets.count()

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
        "can_manage_private_comments": user_can_see_private_comments(request.user),
    }
    return render(request, "apps/projects/apps-projects-overview.html", context)


@has_permission("apps.change_projectlist")
def apps_projects_edit_list_view(request, pk):
    projects = _get_project_or_404_for_user(request, pk)
    technicians = TechnicianUser.objects.all()
    clients = ClientCompany.objects.all().order_by("-name")
    tickets = get_visible_tickets_queryset(request.user)
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
    tickets = get_visible_tickets_queryset(request.user)
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
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            form.save_m2m()
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


@has_permission("apps.delete_projectlist")
def apps_projects_delete_list_view(request, pk):
    projects = _get_project_or_404_for_user(request, pk)
    projects.delete()
    messages.success(request, "Project deleted Successfully!")
    return redirect("apps:projects.list")


@login_required
def apps_projects_comments_view(request, pk):
    projects = _get_project_or_404_for_user(request, pk)

    if request.method != "POST":
        return redirect(reverse("apps:projects.overview", kwargs={"pk": projects.pk}))

    if not request.user.has_perm("apps.add_projectcomment"):
        raise PermissionDenied

    form = ProjectCommentAddForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.project = projects
        comment.save()
        messages.success(request, "Comment inserted Successfully!")
    else:
        messages.error(request, "Something went wrong!")

    return redirect(reverse("apps:projects.overview", kwargs={"pk": projects.pk}))


@login_required
def apps_projects_replies_view(request, pk):
    projects = _get_project_or_404_for_user(request, pk)

    if request.method != "POST":
        return redirect(reverse("apps:projects.overview", kwargs={"pk": projects.pk}))

    if not request.user.has_perm("apps.add_projectcommentreplies"):
        raise PermissionDenied

    comment = get_object_or_404(
        ProjectComment, pk=request.POST.get("comment"), project=projects
    )
    form = ProjectRepliesAddForm(request.POST or None)

    if form.is_valid():
        reply = form.save(commit=False)
        reply.user = request.user
        reply.project = projects
        reply.comment = comment
        reply.save()
        messages.success(request, "Reply inserted Successfully!")
    else:
        messages.error(request, "Something went wrong!")

    return redirect(reverse("apps:projects.overview", kwargs={"pk": projects.pk}))


@has_permission("apps.change_projectlist")
def apps_projects_remove_ticket_view(request, pk):
    ticket = TicketList.objects.get(pk=pk)
    # Find the project that contains this ticket
    project = ProjectList.objects.filter(tickets=ticket).first()

    if not project or not user_can_access_project(request.user, project):
        raise PermissionDenied
    
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


@login_required
def apps_projects_download_file(request, pk):
    project_file = get_object_or_404(ProjectFiles, pk=pk)
    if not project_file.project or not user_can_access_project(request.user, project_file.project):
        raise PermissionDenied
    file_path = project_file.file.path
    response = FileResponse(open(file_path, "rb"))
    response["Content-Type"] = "application/octet-stream"
    response["Content-Disposition"] = f'attachment; filename="{project_file.file.name}"'
    return response


@has_permission("apps.change_projectlist")
def apps_projects_remove_tech_view(request, project_pk, tech_pk):
    project = _get_project_or_404_for_user(request, project_pk)
    technician = TechnicianUser.objects.get(pk=tech_pk)
    technician.projectlist_set.remove(project)
    messages.success(request, "Technician Removed from Project Successfully!")
    return redirect("apps:projects.list")


@login_required
def apps_projects_comments_toggle_visibility_view(request, project_pk, pk):
    projects = _get_project_or_404_for_user(request, project_pk)
    comment = get_object_or_404(ProjectComment, pk=pk, project=projects)
    if not user_can_see_private_comments(request.user):
        raise PermissionDenied
    comment.private = not comment.private
    comment.save()
    if comment.private:
        messages.success(request, "Comment marked as private - hidden from clients!")
    else:
        messages.success(request, "Comment marked as public - visible to all users!")
    return redirect(reverse("apps:projects.overview", kwargs={"pk": projects.pk}))


@login_required
def apps_projects_replies_toggle_visibility_view(request, project_pk, pk):
    projects = _get_project_or_404_for_user(request, project_pk)
    reply = get_object_or_404(ProjectCommentReplies, pk=pk, project=projects)
    if not user_can_see_private_comments(request.user):
        raise PermissionDenied
    reply.private = not reply.private
    reply.save()
    if reply.private:
        messages.success(request, "Reply marked as private - hidden from clients!")
    else:
        messages.success(request, "Reply marked as public - visible to all users!")
    return redirect(reverse("apps:projects.overview", kwargs={"pk": projects.pk}))
