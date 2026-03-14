from django.test import SimpleTestCase

from apps.access import user_can_manage_school_users, user_has_admin_role
from apps.tests import build_user


class ProfileSettingsAccessTests(SimpleTestCase):
    def test_administrator_role_has_profile_settings_access(self):
        user = build_user(groups={"Administrator"})

        self.assertTrue(user_has_admin_role(user))

    def test_super_admin_role_has_profile_settings_access(self):
        user = build_user(groups={"Super Admin"})

        self.assertTrue(user_has_admin_role(user))

    def test_faculty_staff_role_does_not_have_profile_settings_access(self):
        user = build_user(groups={"Faculty/Staff"})

        self.assertFalse(user_has_admin_role(user))

    def test_administrator_with_permission_can_manage_school_users(self):
        user = build_user(
            groups={"Administrator"},
            permissions={"accounts.view_technicianuser"},
        )

        self.assertTrue(user_can_manage_school_users(user))

    def test_administrator_without_permission_cannot_manage_school_users(self):
        user = build_user(groups={"Administrator"})

        self.assertFalse(user_can_manage_school_users(user))

    def test_superuser_can_manage_school_users_without_explicit_permission(self):
        user = build_user(is_superuser=True)

        self.assertTrue(user_can_manage_school_users(user))
