from django import template

from apps.access import user_has_admin_role, user_has_end_user_role

register = template.Library()


@register.filter
def has_admin_or_super_user_role(user):
    return user_has_admin_role(user)


@register.filter
def has_end_user_role(user):
    return user_has_end_user_role(user)
