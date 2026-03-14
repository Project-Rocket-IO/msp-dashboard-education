from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase

from apps.access import (
    get_visible_projects_queryset,
    get_visible_tickets_queryset,
    user_can_access_dashboard,
    user_can_delete_ticket_comment,
    user_can_manage_calendar_event,
    user_has_end_user_role,
    user_has_admin_role,
)
from apps.forms import (
    ProjectCommentAddForm,
    ProjectRepliesAddForm,
    TicketCommentAddForm,
    TicketRepliesAddForm,
)
from apps.views.tickets import (
    _coerce_ticket_id_list,
    _normalize_ticket_upload_choice,
    _rename_ticket_upload_columns,
    TICKET_UPLOAD_PRIORITY_ALIASES,
    TICKET_UPLOAD_STATUS_ALIASES,
)
from dashboards.views import dashboard_analytics_view
from rbac.views import view_home


class FakeGroupQuerySet:
    def __init__(self, exists_result):
        self._exists_result = exists_result

    def exists(self):
        return self._exists_result


class FakeGroups:
    def __init__(self, matching_names=None):
        self.matching_names = set(matching_names or [])

    def filter(self, name__in):
        return FakeGroupQuerySet(bool(self.matching_names.intersection(set(name__in))))


def build_user(
    *,
    user_id=1,
    groups=None,
    is_superuser=False,
    permissions=None,
    email="",
    first_name="",
    last_name="",
    title="",
    **extra_attrs,
):
    permissions = set(permissions or [])
    attributes = {
        "pk": user_id,
        "is_authenticated": True,
        "is_superuser": is_superuser,
        "groups": FakeGroups(groups),
        "has_perm": lambda perm: perm in permissions,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "title": title,
    }
    attributes.update(extra_attrs)
    return SimpleNamespace(**attributes)


class FakeQuerySet:
    def __init__(self):
        self.filtered_args = ()
        self.filtered_kwargs = {}
        self.none_called = False
        self.distinct_called = False

    def none(self):
        self.none_called = True
        return self

    def distinct(self):
        self.distinct_called = True
        return self

    def filter(self, *args, **kwargs):
        self.filtered_args = args
        self.filtered_kwargs = kwargs
        return self


class AccessHelperTests(SimpleTestCase):
    def test_super_admin_counts_as_admin_role(self):
        user = build_user(groups={"Super Admin"})

        self.assertTrue(user_has_admin_role(user))

    def test_delete_own_ticket_comment_requires_matching_author(self):
        user = build_user(
            user_id=10,
            permissions={"apps.delete_own_ticket_comments"},
        )
        own_comment = SimpleNamespace(user_id=10)
        other_comment = SimpleNamespace(user_id=11)

        self.assertTrue(user_can_delete_ticket_comment(user, own_comment))
        self.assertFalse(user_can_delete_ticket_comment(user, other_comment))

    def test_calendar_event_creator_can_manage_their_own_event(self):
        user = build_user(user_id=42)
        event = SimpleNamespace(creator_id=42)

        self.assertTrue(user_can_manage_calendar_event(user, event))

    def test_faculty_staff_counts_as_end_user_role(self):
        user = build_user(groups={"Faculty/Staff"})

        self.assertTrue(user_has_end_user_role(user))

    def test_it_department_keeps_dashboard_access(self):
        user = build_user(groups={"IT Dept"})

        self.assertTrue(user_can_access_dashboard(user))

    def test_faculty_staff_dashboard_access_is_disabled(self):
        user = build_user(groups={"Faculty/Staff"})

        self.assertFalse(user_can_access_dashboard(user))

    @patch("apps.access.get_requester_client_company")
    def test_end_user_ticket_visibility_is_limited_to_requester_and_creator(
        self, mocked_requester_client
    ):
        user = build_user(
            groups={"Faculty/Staff"},
            permissions={"apps.view_ticketlist"},
            technician=SimpleNamespace(pk=99),
        )
        requester_client = SimpleNamespace(pk=55)
        mocked_requester_client.return_value = requester_client
        queryset = FakeQuerySet()

        result = get_visible_tickets_queryset(user, queryset)

        self.assertIs(result, queryset)
        self.assertTrue(queryset.distinct_called)
        self.assertEqual(len(queryset.filtered_args), 1)
        visibility_filter = queryset.filtered_args[0]
        self.assertIn(("client", requester_client), visibility_filter.children)
        self.assertIn(("created_by", user), visibility_filter.children)
        self.assertNotIn(("assignment", user.technician), visibility_filter.children)

    def test_end_user_projects_are_hidden_even_with_project_permission(self):
        user = build_user(
            groups={"Faculty/Staff"},
            permissions={"apps.view_projectlist"},
        )
        queryset = FakeQuerySet()

        result = get_visible_projects_queryset(user, queryset)

        self.assertIs(result, queryset)
        self.assertTrue(queryset.none_called)


class DashboardRedirectTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_home_redirects_faculty_staff_to_ticket_list(self):
        request = self.factory.get("/")
        request.user = build_user(groups={"Faculty/Staff"})

        response = view_home(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/apps/support-tickets/list/")

    def test_dashboard_view_redirects_end_users_to_ticket_list(self):
        request = self.factory.get("/")
        request.user = build_user(groups={"Faculty/Staff"})

        response = dashboard_analytics_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/apps/support-tickets/list/")


class CommentFormTests(SimpleTestCase):
    def test_ticket_comment_form_only_exposes_body(self):
        self.assertEqual(list(TicketCommentAddForm().fields), ["body"])

    def test_ticket_reply_form_only_exposes_body(self):
        self.assertEqual(list(TicketRepliesAddForm().fields), ["body"])

    def test_project_comment_form_only_exposes_body(self):
        self.assertEqual(list(ProjectCommentAddForm().fields), ["body"])

    def test_project_reply_form_only_exposes_body(self):
        self.assertEqual(list(ProjectRepliesAddForm().fields), ["body"])


class TicketUploadHelperTests(SimpleTestCase):
    def test_rename_ticket_upload_columns_maps_common_aliases(self):
        renamed = _rename_ticket_upload_columns(
            ["Ticket Name", "User Email", "Assigned To", "Due Date"]
        )

        self.assertEqual(
            renamed,
            {
                "Ticket Name": "name",
                "User Email": "client_email",
                "Assigned To": "technician",
                "Due Date": "due_date",
            },
        )

    def test_status_aliases_map_to_supported_ticket_statuses(self):
        valid_statuses = [
            "New",
            "In Progress",
            "Scheduled",
            "Postponed",
            "Waiting on Client",
            "Waiting on Vendor",
            "Follow-Up",
            "Need to Post",
            "Completed",
            "Closed",
        ]

        self.assertEqual(
            _normalize_ticket_upload_choice(
                "waiting on user",
                "status",
                valid_statuses,
                aliases=TICKET_UPLOAD_STATUS_ALIASES,
            ),
            "Waiting on Client",
        )

    def test_invalid_priority_value_raises_clear_error(self):
        with self.assertRaisesMessage(ValueError, "Priority 'Impossible' is not valid."):
            _normalize_ticket_upload_choice(
                "Impossible",
                "priority",
                ["Emergency", "High", "Medium", "Low"],
                aliases=TICKET_UPLOAD_PRIORITY_ALIASES,
            )

    def test_ticket_id_list_keeps_only_unique_numeric_ids(self):
        self.assertEqual(
            _coerce_ticket_id_list(["10", "10", "", "abc", 14]),
            [10, 14],
        )
