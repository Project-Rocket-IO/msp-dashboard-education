from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.access import user_can_manage_calendar_event
from apps.tests import build_user


class CalendarAccessTests(SimpleTestCase):
    def test_calendar_manager_group_can_manage_other_events(self):
        user = build_user(groups={"IT Dept"})
        event = SimpleNamespace(creator_id=999)

        self.assertTrue(user_can_manage_calendar_event(user, event))

    def test_non_manager_cannot_manage_someone_elses_event(self):
        user = build_user(groups={"Faculty/Staff"}, user_id=10)
        event = SimpleNamespace(creator_id=11)

        self.assertFalse(user_can_manage_calendar_event(user, event))
