from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import *
from django.db.models.functions import *
from django.db.models import Prefetch
from django.shortcuts import redirect, render, reverse
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404
from apps.models import (
    ProjectList,
    TicketComment,
    TicketCommentReplies,
    TechnicianLabor,
    TicketFiles,
    TicketList,
    ClientCompany,
    PRIORITY,
    TICKET_STATUS,
    TYPE_CHOICE,
)
from accounts.models import TechnicianUser
from apps.forms import TicketCommentAddForm, TicketListAddForm, TicketRepliesAddForm
from django.contrib import messages
from datetime import date, datetime
from rbac.decorators import has_permission
from rbac.utils import paginate_queryset
from django.core.exceptions import PermissionDenied
import json
import os
import re
import tempfile
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from apps.access import (
    get_requester_client_company,
    get_visible_tickets_queryset,
    user_can_access_ticket,
    user_can_delete_ticket_comment,
    user_has_end_user_role,
    user_can_see_private_comments,
)

# Try to import pandas for Excel processing
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


TICKET_UPLOAD_COLUMN_ALIASES = {
    "name": {"name", "ticket", "ticket_name", "ticketname", "ticket_title", "title", "subject"},
    "client": {"client", "client_name", "user", "user_name", "student", "faculty", "staff", "administrator", "person", "requester", "requester_name"},
    "client_email": {"client_email", "email", "user_email", "requester_email"},
    "client_id": {"client_id", "clientid", "user_id", "userid", "person_id", "personid"},
    "client_first_name": {"client_first_name", "user_first_name", "first_name", "firstname", "requester_first_name"},
    "client_last_name": {"client_last_name", "user_last_name", "last_name", "lastname", "requester_last_name"},
    "technician": {"technician", "technician_name", "assigned_to", "assignedto", "assignee", "owner", "assignment", "main_tech"},
    "technician_email": {"technician_email", "assignee_email", "owner_email"},
    "technician_id": {"technician_id", "technicianid", "assignee_id", "owner_id"},
    "description": {"description", "details", "body", "notes"},
    "due_date": {"due_date", "duedate", "due", "target_date"},
    "ticket_type": {"ticket_type", "tickettype", "type"},
    "status": {"status", "ticket_status"},
    "priority": {"priority", "severity", "urgency"},
    "tags": {"tag", "tags", "labels"},
}

TICKET_UPLOAD_STATUS_ALIASES = {
    "open": "New",
    "inprogress": "In Progress",
    "progress": "In Progress",
    "waitingonuser": "Waiting on Client",
    "waitingonclient": "Waiting on Client",
    "waitingonvendor": "Waiting on Vendor",
    "followup": "Follow-Up",
    "needtopost": "Need to Post",
}

TICKET_UPLOAD_PRIORITY_ALIASES = {
    "urgent": "Emergency",
    "critical": "Emergency",
    "normal": "Medium",
    "med": "Medium",
}

TICKET_UPLOAD_TYPE_ALIASES = {
    "full": "Full Time",
    "fulltime": "Full Time",
    "part": "Part Time",
    "parttime": "Part Time",
}

TICKET_UPLOAD_DATE_FORMATS = (
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d %b %Y",
    "%b %d %Y",
)


#########
# TICKETS
def _get_ticket_or_404_for_user(request, pk):
    return get_object_or_404(get_visible_tickets_queryset(request.user), pk=pk)


def _get_ticket_comments_queryset(ticket, user):
    comments = TicketComment.objects.filter(ticket=ticket).order_by("date_added")
    if user_can_see_private_comments(user):
        return comments
    return comments.filter(private=False)


def _get_ticket_replies_queryset(ticket, user):
    replies = TicketCommentReplies.objects.filter(ticket=ticket).order_by("date_added")
    if user_can_see_private_comments(user):
        return replies
    return replies.filter(private=False)


def _request_wants_json(request):
    accepts = request.headers.get("Accept", "")
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or "application/json" in accepts
    )


def _normalize_ticket_upload_header(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _normalize_ticket_upload_token(value):
    cleaned = str(value).strip().lower()
    return re.sub(r"[^a-z0-9]+", "", cleaned)


def _rename_ticket_upload_columns(columns):
    renamed = {}
    for column in columns:
        normalized = _normalize_ticket_upload_header(column)
        canonical = next(
            (
                name
                for name, aliases in TICKET_UPLOAD_COLUMN_ALIASES.items()
                if normalized in aliases
            ),
            normalized,
        )
        renamed[column] = canonical
    return renamed


def _coerce_upload_value(value):
    if value is None:
        return ""
    if pd is not None and pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"", "nan", "nat", "none", "null"}:
        return ""
    return text


def _coerce_upload_id_value(value):
    if value is None or (pd is not None and pd.isna(value)):
        return ""

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else str(value)

    text = _coerce_upload_value(value)
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def _coerce_ticket_id_list(raw_ids):
    if isinstance(raw_ids, str):
        raw_ids = [raw_ids]

    ticket_ids = []
    for raw_id in raw_ids or []:
        value = _coerce_upload_id_value(raw_id)
        if not value:
            continue
        try:
            ticket_ids.append(int(value))
        except (TypeError, ValueError):
            continue

    return list(dict.fromkeys(ticket_ids))


def _split_upload_values(raw_value):
    value = _coerce_upload_value(raw_value)
    if not value:
        return []
    return [
        item.strip()
        for item in re.split(r"[,\n;|]+", value)
        if item and item.strip()
    ]


def _normalize_ticket_upload_choice(raw_value, field_label, valid_values, aliases=None):
    value = _coerce_upload_value(raw_value)
    if not value:
        return None

    aliases = aliases or {}
    value_map = {
        _normalize_ticket_upload_token(valid_value): valid_value
        for valid_value in valid_values
    }
    value_map.update(
        {
            _normalize_ticket_upload_token(alias): target
            for alias, target in aliases.items()
        }
    )

    normalized_value = value_map.get(_normalize_ticket_upload_token(value))
    if normalized_value:
        return normalized_value

    raise ValueError(
        f"{field_label.title()} '{value}' is not valid. Use one of: {', '.join(valid_values)}."
    )


def _parse_ticket_upload_date(raw_value):
    if raw_value is None or (pd is not None and pd.isna(raw_value)):
        return None

    if isinstance(raw_value, datetime):
        return raw_value.date()
    if isinstance(raw_value, date):
        return raw_value

    if pd is not None:
        try:
            parsed_value = pd.to_datetime(raw_value, errors="raise")
            if not pd.isna(parsed_value):
                return parsed_value.date()
        except Exception:
            pass

    text_value = _coerce_upload_value(raw_value)
    if not text_value:
        return None

    for fmt in TICKET_UPLOAD_DATE_FORMATS:
        try:
            return datetime.strptime(text_value, fmt).date()
        except ValueError:
            continue

    raise ValueError(
        f"Due date '{text_value}' is not valid. Use YYYY-MM-DD or a standard Excel date."
    )


def _match_client_candidates(*, client_id="", client_email="", client_name=""):
    queryset = ClientCompany.objects.all()

    if client_id:
        if not client_id.isdigit():
            raise ValueError(f"Client ID '{client_id}' is not numeric.")
        return queryset.filter(pk=int(client_id))

    if client_email:
        return queryset.filter(email__iexact=client_email)

    if client_name:
        by_name = queryset.filter(name__iexact=client_name)
        if by_name.exists():
            return by_name

        full_name_match = queryset.annotate(
            full_name=Concat("contact_first", Value(" "), "contact_last")
        ).filter(full_name__iexact=client_name)
        if full_name_match.exists():
            return full_name_match

    return queryset.none()


def _resolve_ticket_upload_client(row):
    client_id = _coerce_upload_id_value(row.get("client_id"))
    client_email = _coerce_upload_value(row.get("client_email"))
    client_name = _coerce_upload_value(row.get("client"))

    if not client_name:
        first_name = _coerce_upload_value(row.get("client_first_name"))
        last_name = _coerce_upload_value(row.get("client_last_name"))
        client_name = " ".join(part for part in (first_name, last_name) if part).strip()

    if not any([client_id, client_email, client_name]):
        raise ValueError(
            "Missing user reference. Include client, client_email, client_id, or first/last name columns."
        )

    matches = _match_client_candidates(
        client_id=client_id,
        client_email=client_email,
        client_name=client_name,
    )

    match_count = matches.count()
    if match_count == 1:
        return matches.first()
    if match_count > 1:
        raise ValueError(
            "User reference matched multiple records. Use client_email or client_id to make it unique."
        )

    reference = client_email or client_id or client_name
    raise ValueError(
        f"User '{reference}' was not found. Create the user first or use an existing client_email/client_id."
    )


def _match_technician_candidates(reference):
    queryset = TechnicianUser.objects.select_related("auth_user")
    if reference.isdigit():
        return queryset.filter(pk=int(reference))

    by_login = queryset.filter(
        Q(auth_user__username__iexact=reference)
        | Q(auth_user__email__iexact=reference)
    )
    if by_login.exists():
        return by_login

    full_name_match = queryset.annotate(
        full_name=Concat("auth_user__first_name", Value(" "), "auth_user__last_name")
    ).filter(full_name__iexact=reference)
    if full_name_match.exists():
        return full_name_match

    return queryset.none()


def _resolve_ticket_upload_technicians(row, client):
    references = []

    technician_id = _coerce_upload_id_value(row.get("technician_id"))
    technician_email = _coerce_upload_value(row.get("technician_email"))
    technician_name = row.get("technician")

    if technician_id:
        references.extend(_split_upload_values(technician_id))
    if technician_email:
        references.extend(_split_upload_values(technician_email))
    if technician_name:
        references.extend(_split_upload_values(technician_name))

    if not references:
        return [client.main_tech] if client.main_tech else []

    resolved = []
    for reference in references:
        matches = _match_technician_candidates(reference)
        match_count = matches.count()
        if match_count == 1:
            resolved.append(matches.first())
            continue
        if match_count > 1:
            raise ValueError(
                f"Technician '{reference}' matched multiple records. Use a username, email, or technician_id."
            )
        raise ValueError(
            f"Technician '{reference}' was not found. Use an existing username, email, or technician_id."
        )

    return list({tech.pk: tech for tech in resolved}.values())


def _format_ticket_form_errors(form):
    return {
        field: [error["message"] for error in errors]
        for field, errors in form.errors.get_json_data().items()
    }


def _user_can_manage_ticket_fields(user):
    return (
        bool(user)
        and getattr(user, "is_authenticated", False)
        and not user_has_end_user_role(user)
        and user.has_perm("apps.change_ticketlist")
    )


def _user_can_bulk_upload_tickets(user):
    return (
        bool(user)
        and getattr(user, "is_authenticated", False)
        and not user_has_end_user_role(user)
        and user.has_perm("apps.add_ticketlist")
    )


def _user_can_bulk_delete_tickets(user):
    return (
        bool(user)
        and getattr(user, "is_authenticated", False)
        and not user_has_end_user_role(user)
        and user.has_perm("apps.delete_ticketlist")
    )


def _user_can_manage_ticket_files(user):
    return (
        bool(user)
        and getattr(user, "is_authenticated", False)
        and not user_has_end_user_role(user)
        and (
            user.has_perm("apps.change_ticketlist")
            or user.has_perm("apps.delete_ticketlist")
        )
    )


def _build_ticket_role_context(user):
    requester_client = get_requester_client_company(user)
    can_edit_ticket_fields = _user_can_manage_ticket_fields(user)

    return {
        "is_end_user_role": user_has_end_user_role(user),
        "requester_client": requester_client,
        "can_bulk_upload_tickets": _user_can_bulk_upload_tickets(user),
        "can_bulk_delete_tickets": _user_can_bulk_delete_tickets(user),
        "can_edit_ticket_fields": can_edit_ticket_fields,
        "can_log_ticket_labor": can_edit_ticket_fields,
        "can_upload_ticket_files": user.has_perm("apps.add_ticketfiles"),
        "can_manage_ticket_files": _user_can_manage_ticket_files(user),
    }


@login_required
def apps_tickets_comments_delete_view(request, ticket_pk, pk):
    tickets = _get_ticket_or_404_for_user(request, ticket_pk)
    comment = get_object_or_404(TicketComment, pk=pk, ticket=tickets)

    if request.method != "POST":
        return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))

    if not user_can_delete_ticket_comment(request.user, comment):
        raise PermissionDenied

    comment.delete()
    return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))


@login_required
def apps_tickets_comments_toggle_visibility_view(request, ticket_pk, pk):
    tickets = _get_ticket_or_404_for_user(request, ticket_pk)
    comment = get_object_or_404(TicketComment, pk=pk, ticket=tickets)

    if not user_can_see_private_comments(request.user):
        raise PermissionDenied

    comment.private = not comment.private
    comment.save()

    if comment.private:
        messages.success(request, "Comment marked as private - hidden from clients!")
    else:
        messages.success(request, "Comment marked as public - visible to all users!")

    return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))


@login_required
def apps_tickets_replies_toggle_visibility_view(request, ticket_pk, pk):
    tickets = _get_ticket_or_404_for_user(request, ticket_pk)
    reply = get_object_or_404(TicketCommentReplies, pk=pk, ticket=tickets)

    if not user_can_see_private_comments(request.user):
        raise PermissionDenied

    reply.private = not reply.private
    reply.save()

    if reply.private:
        messages.success(request, "Reply marked as private - hidden from clients!")
    else:
        messages.success(request, "Reply marked as public - visible to all users!")

    return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))


@login_required
def apps_tickets_comments_view(request, pk):
    tickets = _get_ticket_or_404_for_user(request, pk)

    if request.method != "POST":
        return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))

    if not request.user.has_perm("apps.add_ticketcomment"):
        raise PermissionDenied

    form = TicketCommentAddForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.ticket = tickets
        comment.save()
        messages.success(request, "Comment inserted Successfully!")
    else:
        messages.error(request, "Something went wrong!")

    return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))


@login_required
def apps_tickets_replies_view(request, pk):
    tickets = _get_ticket_or_404_for_user(request, pk)

    if request.method != "POST":
        return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))

    if not request.user.has_perm("apps.add_ticketcommentreplies"):
        raise PermissionDenied

    comment = get_object_or_404(TicketComment, pk=request.POST.get("comment"), ticket=tickets)
    form = TicketRepliesAddForm(request.POST or None)

    if form.is_valid():
        reply = form.save(commit=False)
        reply.user = request.user
        reply.ticket = tickets
        reply.comment = comment
        reply.save()
        messages.success(request, "Reply inserted Successfully!")
    else:
        messages.error(request, "Something went wrong!")

    return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))


@login_required
def apps_tickets_details_view(request, pk):
    tickets = _get_ticket_or_404_for_user(request, pk)
    ticket_files = TicketFiles.objects.filter(ticket_id=pk)
    projects = ProjectList.objects.filter(pk=tickets.project_id)
    comments = _get_ticket_comments_queryset(tickets, request.user)
    replies = _get_ticket_replies_queryset(tickets, request.user)

    # Labor entries for this ticket (for combined activity feed)
    labor_entries = TechnicianLabor.objects.filter(ticket=tickets).select_related(
        "created_by", "created_by__auth_user", "submitted_by"
    ).order_by("created_at")

    # Combined activity feed: comments + labor, sorted by date (oldest first)
    activity_feed = []
    for c in comments:
        activity_feed.append({"type": "comment", "date": c.date_added, "obj": c})
    for labor in labor_entries:
        activity_feed.append({
            "type": "labor",
            "date": labor.created_at,
            "obj": labor,
            "labor_hours": labor.minutes // 60,
            "labor_minutes": labor.minutes % 60,
        })
    activity_feed.sort(key=lambda x: x["date"])
    
    technicians = TechnicianUser.objects.all()
    context = {
        "tickets": tickets,
        "comments": comments,
        "activity_feed": activity_feed,
        "projects": projects,
        "replies": replies,
        "technicians": technicians,
        "ticket_files": ticket_files,
        "today": date.today(),
        "can_manage_private_comments": user_can_see_private_comments(request.user),
    }
    context.update(_build_ticket_role_context(request.user))

    if request.method == "POST":
        if not _user_can_manage_ticket_fields(request.user):
            raise PermissionDenied

        form = TicketListAddForm(
            request.POST or None, request.FILES or None, instance=tickets
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Ticket Updates Successfully!")
            return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))
        else:
            messages.error(request, "Something went wrong!")
            return redirect(reverse("apps:tickets.details", kwargs={"pk": tickets.pk}))
    return render(request, "apps/support-tickets/apps-tickets-details.html", context)


def get_ticket_list_data(request, per_page=10):
    base_queryset = (
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
    all_tickets = get_visible_tickets_queryset(request.user, base_queryset)

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
    context.update(_build_ticket_role_context(request.user))



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
        requester_client = None
        form_data = request.POST
        if user_has_end_user_role(request.user):
            requester_client = get_requester_client_company(request.user)
            if not requester_client:
                message = (
                    "Your account is not linked to a school user profile yet. "
                    "Please contact your IT department before creating tickets."
                )
                if _request_wants_json(request):
                    return JsonResponse(
                        {"success": False, "message": message},
                        status=400,
                    )
                messages.error(request, message)
                return redirect("apps:tickets.list")

            form_data = request.POST.copy()
            form_data["client"] = str(requester_client.pk)
            form_data["status"] = "New"
            if requester_client.main_tech_id:
                form_data.setlist("assignment", [str(requester_client.main_tech_id)])
            else:
                form_data.setlist("assignment", [])

        form = TicketListAddForm(form_data, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            if requester_client is not None:
                ticket.client = requester_client
                ticket.status = "New"

            ticket.created_by = request.user
            ticket.save()
            form.save_m2m()
            if requester_client is not None:
                if requester_client.main_tech_id:
                    ticket.assignment.set([requester_client.main_tech])
                else:
                    ticket.assignment.clear()
            for file in request.FILES.getlist("files"):
                if file:
                    file.name = file.name[:100]  # Truncate filename if necessary
                    TicketFiles.objects.create(file=file, ticket=ticket)
            if _request_wants_json(request):
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Ticket created successfully.",
                        "redirect_url": reverse("apps:tickets.list"),
                        "ticket_id": ticket.pk,
                    }
                )
            messages.success(request, "Ticket Created!")
            return redirect("apps:tickets.list")
        else:
            if _request_wants_json(request):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Please correct the highlighted ticket fields.",
                        "errors": _format_ticket_form_errors(form),
                    },
                    status=400,
                )
            messages.error(request, "Something went wrong!")
            print(form.errors)
            return redirect("apps:tickets.list")

    if _request_wants_json(request):
        return JsonResponse(
            {"success": False, "message": "Invalid request method."}, status=405
        )
    return redirect("apps:tickets.list")


@has_permission("apps.close_ticketlist")
def apps_tickets_close_view(request, pk):
    if user_has_end_user_role(request.user):
        raise PermissionDenied
    ticket = _get_ticket_or_404_for_user(request, pk)
    ticket.status = "Closed"
    ticket.save()
    messages.success(request, "Tickets status set to Closed Successfully!")
    return redirect("apps:tickets.list")


@has_permission("apps.complete_ticketlist")
def apps_tickets_complete_view(request, pk):
    if user_has_end_user_role(request.user):
        raise PermissionDenied
    ticket = _get_ticket_or_404_for_user(request, pk)
    ticket.status = "Completed"
    ticket.save()
    messages.success(request, "Tickets status set to Completed Successfully!")
    return redirect("apps:tickets.list")


@has_permission("apps.change_ticketlist")
def apps_tickets_edit_view(request, pk):
    if user_has_end_user_role(request.user):
        raise PermissionDenied
    tickets = _get_ticket_or_404_for_user(request, pk)
    technicians = TechnicianUser.objects.all()
    projects = ProjectList.objects.all()
    clients = ClientCompany.objects.all()
    comments = _get_ticket_comments_queryset(tickets, request.user)
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
            return redirect("apps:tickets.details", pk=ticket.pk)

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
    if user_has_end_user_role(request.user):
        raise PermissionDenied
    tickets = _get_ticket_or_404_for_user(request, pk)
    tickets.delete()
    messages.success(request, "Tickets deleted Successfully!")
    return redirect("apps:tickets.list")


@has_permission("apps.delete_ticketlist")
def apps_tickets_bulk_delete_view(request):
    if user_has_end_user_role(request.user):
        raise PermissionDenied

    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "Invalid request method."}, status=405
        )

    try:
        if request.content_type and "application/json" in request.content_type:
            payload = json.loads(request.body.decode("utf-8") or "{}")
            ticket_ids = _coerce_ticket_id_list(payload.get("ticket_ids", []))
        else:
            ticket_ids = _coerce_ticket_id_list(
                request.POST.getlist("ticket_ids")
                or request.POST.getlist("ticket_ids[]")
            )
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid delete request payload."},
            status=400,
        )

    if not ticket_ids:
        return JsonResponse(
            {"success": False, "message": "Select at least one ticket to delete."},
            status=400,
        )

    visible_tickets = get_visible_tickets_queryset(request.user).filter(pk__in=ticket_ids)
    found_ids = set(visible_tickets.values_list("pk", flat=True))
    missing_ids = sorted(set(ticket_ids) - found_ids)
    deleted_count = visible_tickets.count()

    if not deleted_count:
        return JsonResponse(
            {
                "success": False,
                "message": "The selected tickets could not be deleted.",
                "missing_ids": missing_ids,
            },
            status=404,
        )

    visible_tickets.delete()

    message = f"Deleted {deleted_count} ticket(s)."
    if missing_ids:
        message += (
            f" {len(missing_ids)} ticket(s) were skipped because they were unavailable."
        )

    return JsonResponse(
        {
            "success": True,
            "message": message,
            "deleted_count": deleted_count,
            "missing_ids": missing_ids,
        }
    )


@login_required
def apps_ticket_download_file(request, pk):
    file_obj = get_object_or_404(TicketFiles, pk=pk)
    if not file_obj.ticket or not user_can_access_ticket(request.user, file_obj.ticket):
        raise PermissionDenied
    response = FileResponse(file_obj.file, as_attachment=True)
    return response


@login_required
def apps_ticket_file_upload_view(request, pk):
    ticket = _get_ticket_or_404_for_user(request, pk)

    if request.method != "POST":
        return redirect(reverse("apps:tickets.details", kwargs={"pk": ticket.pk}))

    if not request.user.has_perm("apps.add_ticketfiles"):
        raise PermissionDenied

    files = request.FILES.getlist("files")
    if not files:
        messages.error(request, "Select at least one file to upload.")
        return redirect(reverse("apps:tickets.details", kwargs={"pk": ticket.pk}))

    uploaded_count = 0
    for file in files:
        if not file:
            continue
        file.name = file.name[:100]
        TicketFiles.objects.create(file=file, ticket=ticket)
        uploaded_count += 1

    if uploaded_count:
        messages.success(request, f"Uploaded {uploaded_count} file(s) successfully.")
    else:
        messages.error(request, "No files were uploaded.")

    return redirect(reverse("apps:tickets.details", kwargs={"pk": ticket.pk}))


@has_permission("apps.change_ticketlist")
def apps_ticket_file_rename_view(request, pk):
    """Rename a ticket file"""
    if user_has_end_user_role(request.user):
        raise PermissionDenied

    if request.method == "POST":
        file_obj = get_object_or_404(TicketFiles, pk=pk)
        if not file_obj.ticket or not user_can_access_ticket(request.user, file_obj.ticket):
            raise PermissionDenied
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
    if user_has_end_user_role(request.user):
        raise PermissionDenied

    if request.method == "POST":
        file_obj = get_object_or_404(TicketFiles, pk=pk)
        if not file_obj.ticket or not user_can_access_ticket(request.user, file_obj.ticket):
            raise PermissionDenied
        
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
    if user_has_end_user_role(request.user):
        raise PermissionDenied

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
                df = df.rename(columns=_rename_ticket_upload_columns(df.columns))

                if df.empty:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "The spreadsheet is empty. Add at least one ticket row before uploading.",
                        },
                        status=400,
                    )

                missing_requirements = []
                if "name" not in df.columns:
                    missing_requirements.append(
                        "a ticket title column such as name, title, ticket name, or subject"
                    )
                if not any(
                    column in df.columns
                    for column in (
                        "client",
                        "client_email",
                        "client_id",
                        "client_first_name",
                        "client_last_name",
                    )
                ):
                    missing_requirements.append(
                        "a user reference column such as client, user, client_email, or client_id"
                    )

                if missing_requirements:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Missing required spreadsheet fields: "
                            + "; ".join(missing_requirements)
                            + ".",
                        },
                        status=400,
                    )
                 
                created_count = 0
                errors = []
                valid_statuses = [choice for choice, _ in TICKET_STATUS]
                valid_priorities = [choice for choice, _ in PRIORITY]
                valid_types = [choice for choice, _ in TYPE_CHOICE]
                 
                for index, row in df.iterrows():
                    try:
                        row_number = index + 2
                        ticket_name = _coerce_upload_value(row.get("name"))
                        if not ticket_name:
                            raise ValueError("Ticket title cannot be empty.")

                        client = _resolve_ticket_upload_client(row)
                        technicians = _resolve_ticket_upload_technicians(row, client)

                        with transaction.atomic():
                            ticket = TicketList(
                                name=ticket_name,
                                client=client,
                                created_by=request.user,
                                description=_coerce_upload_value(row.get("description")),
                                status="New",
                                priority="Medium",
                            )

                            ticket_type = _normalize_ticket_upload_choice(
                                row.get("ticket_type"),
                                "ticket type",
                                valid_types,
                                aliases=TICKET_UPLOAD_TYPE_ALIASES,
                            )
                            if ticket_type:
                                ticket.ticket_type = ticket_type

                            status = _normalize_ticket_upload_choice(
                                row.get("status"),
                                "status",
                                valid_statuses,
                                aliases=TICKET_UPLOAD_STATUS_ALIASES,
                            )
                            if status:
                                ticket.status = status

                            priority = _normalize_ticket_upload_choice(
                                row.get("priority"),
                                "priority",
                                valid_priorities,
                                aliases=TICKET_UPLOAD_PRIORITY_ALIASES,
                            )
                            if priority:
                                ticket.priority = priority

                            due_date = _parse_ticket_upload_date(row.get("due_date"))
                            if due_date:
                                ticket.due_date = due_date

                            ticket.save()
                            if technicians:
                                ticket.assignment.set(technicians)

                            tags = _split_upload_values(row.get("tags"))
                            if tags:
                                ticket.tag.add(*tags)

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
                        "message": "No tickets were created. Please check the spreadsheet field names and row data.",
                        "errors": errors,
                    }, status=400)
                         
            except Exception as e:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                message = f"Error processing Excel file: {str(e)}"
                if "openpyxl" in str(e).lower():
                    message = (
                        "Error processing Excel file: the Excel reader dependency is unavailable. "
                        "Install or enable openpyxl in the app container."
                    )
                return JsonResponse({
                    "success": False,
                    "message": message
                }, status=400)
                    
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }, status=500)
    
    return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)
