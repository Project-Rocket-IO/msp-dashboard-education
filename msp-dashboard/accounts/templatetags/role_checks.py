from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter
def has_admin_or_super_user_role(user):
    """
    Check if user has Administrator or Super User role
    """
    if not user.is_authenticated:
        return False
    
    # Check if user is superuser
    if user.is_superuser:
        return True
    
    # Check if user has Administrator or Super User group
    admin_group = Group.objects.filter(name='Administrator').first()
    super_user_group = Group.objects.filter(name='Super User').first()
    
    if admin_group and user.groups.filter(id=admin_group.id).exists():
        return True
    
    if super_user_group and user.groups.filter(id=super_user_group.id).exists():
        return True
    
    return False 