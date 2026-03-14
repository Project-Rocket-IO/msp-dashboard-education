from django.db.models import Q


ADMIN_GROUP_NAMES = ("Administrator", "Super Admin", "Super User")
END_USER_GROUP_NAMES = ("Student", "Faculty/Staff")
PRIVATE_COMMENT_VIEWER_GROUPS = ("IT Dept",) + ADMIN_GROUP_NAMES
CALENDAR_MANAGER_GROUPS = ("IT Dept",) + ADMIN_GROUP_NAMES
STUDENT_ASSIGNMENT_PREFIX = "Assigned to: "


def user_in_groups(user, group_names):
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return user.groups.filter(name__in=group_names).exists()


def user_has_admin_role(user):
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return getattr(user, "is_superuser", False) or user_in_groups(user, ADMIN_GROUP_NAMES)


def user_has_end_user_role(user):
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return user_in_groups(user, END_USER_GROUP_NAMES)


def user_should_land_in_ticket_list(user):
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return user_has_end_user_role(user) or hasattr(user, "client")


def user_can_access_dashboard(user):
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return not user_should_land_in_ticket_list(user)


def user_can_manage_school_users(user):
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False):
        return True

    return user_has_admin_role(user) and user.has_perm("accounts.view_technicianuser")


def user_can_see_private_comments(user):
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return getattr(user, "is_superuser", False) or user_in_groups(
        user, PRIVATE_COMMENT_VIEWER_GROUPS
    )


def get_assigned_client_company(user):
    if not user or not getattr(user, "is_authenticated", False):
        return None

    title = getattr(user, "title", "") or ""
    if not title.startswith(STUDENT_ASSIGNMENT_PREFIX):
        return None

    client_name = title.removeprefix(STUDENT_ASSIGNMENT_PREFIX).strip()
    if not client_name:
        return None

    from apps.models import ClientCompany

    try:
        return ClientCompany.objects.get(name=client_name)
    except ClientCompany.DoesNotExist:
        return None
    except ClientCompany.MultipleObjectsReturned:
        return ClientCompany.objects.filter(name=client_name).order_by("id").first()


def get_requester_client_company(user):
    if not user or not getattr(user, "is_authenticated", False):
        return None

    if hasattr(user, "client") and user.client.company_id:
        return user.client.company

    assigned_client = get_assigned_client_company(user)
    if assigned_client:
        return assigned_client

    from apps.models import ClientCompany

    email = (getattr(user, "email", "") or "").strip()
    if email:
        matched_by_email = (
            ClientCompany.objects.filter(email__iexact=email).order_by("id").first()
        )
        if matched_by_email:
            return matched_by_email

    first_name = (getattr(user, "first_name", "") or "").strip()
    last_name = (getattr(user, "last_name", "") or "").strip()
    full_name = " ".join(part for part in (first_name, last_name) if part).strip()

    if full_name:
        matched_by_name = (
            ClientCompany.objects.filter(name__iexact=full_name).order_by("id").first()
        )
        if matched_by_name:
            return matched_by_name

    if first_name and last_name:
        return (
            ClientCompany.objects.filter(
                contact_first__iexact=first_name,
                contact_last__iexact=last_name,
            )
            .order_by("id")
            .first()
        )

    return None


def get_visible_tickets_queryset(user, base_queryset=None):
    from apps.models import TicketList

    queryset = base_queryset if base_queryset is not None else TicketList.objects.all()

    if not user or not getattr(user, "is_authenticated", False):
        return queryset.none()

    if getattr(user, "is_superuser", False):
        return queryset.distinct()

    visibility_filter = Q()
    has_visibility_rule = False

    requester_client = get_requester_client_company(user)
    if user_has_end_user_role(user):
        if not (
            user.has_perm("apps.view_own_ticketlist")
            or user.has_perm("apps.view_ticketlist")
        ):
            return queryset.none()

        if requester_client:
            visibility_filter |= Q(client=requester_client)
            has_visibility_rule = True

        if hasattr(TicketList, "created_by"):
            visibility_filter |= Q(created_by=user)
            has_visibility_rule = True

        if not has_visibility_rule:
            return queryset.none()

        return queryset.filter(visibility_filter).distinct()

    if user.has_perm("apps.view_ticketlist"):
        return queryset.distinct()

    if not user.has_perm("apps.view_own_ticketlist"):
        return queryset.none()

    if hasattr(user, "client") and user.client.company_id:
        visibility_filter |= Q(client=user.client.company)
        has_visibility_rule = True

    if requester_client:
        visibility_filter |= Q(client=requester_client)
        has_visibility_rule = True

    if hasattr(user, "technician"):
        visibility_filter |= Q(assignment=user.technician)
        has_visibility_rule = True

    if hasattr(TicketList, "created_by"):
        visibility_filter |= Q(created_by=user)
        has_visibility_rule = True

    if not has_visibility_rule:
        return queryset.none()

    return queryset.filter(visibility_filter).distinct()


def get_visible_projects_queryset(user, base_queryset=None):
    from apps.models import ProjectList

    queryset = base_queryset if base_queryset is not None else ProjectList.objects.all()

    if not user or not getattr(user, "is_authenticated", False):
        return queryset.none()

    if getattr(user, "is_superuser", False):
        return queryset.distinct()

    if user_has_end_user_role(user):
        return queryset.none()

    if user.has_perm("apps.view_projectlist"):
        return queryset.distinct()

    if not user.has_perm("apps.view_own_projects"):
        return queryset.none()

    visibility_filter = Q()
    has_visibility_rule = False

    if hasattr(user, "client") and user.client.company_id:
        visibility_filter |= Q(client=user.client.company)
        has_visibility_rule = True

    requester_client = get_requester_client_company(user)
    if requester_client:
        visibility_filter |= Q(client=requester_client)
        has_visibility_rule = True

    if hasattr(user, "technician"):
        visibility_filter |= Q(assignment=user.technician)
        has_visibility_rule = True

    if hasattr(ProjectList, "created_by"):
        visibility_filter |= Q(created_by=user)
        has_visibility_rule = True

    if not has_visibility_rule:
        return queryset.none()

    return queryset.filter(visibility_filter).distinct()


def user_can_access_ticket(user, ticket):
    return get_visible_tickets_queryset(user).filter(pk=ticket.pk).exists()


def user_can_access_project(user, project):
    return get_visible_projects_queryset(user).filter(pk=project.pk).exists()


def user_can_delete_ticket_comment(user, comment):
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False) or user.has_perm("apps.delete_ticketcomment"):
        return True

    return user.has_perm("apps.delete_own_ticket_comments") and comment.user_id == user.pk


def user_can_manage_calendar_event(user, event):
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False):
        return True

    if user_in_groups(user, CALENDAR_MANAGER_GROUPS):
        return True

    return event.creator_id == user.pk
