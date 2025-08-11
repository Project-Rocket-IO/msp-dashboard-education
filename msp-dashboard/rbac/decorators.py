from functools import wraps
from django.core.exceptions import PermissionDenied

def has_permission(*permissions_codename, condition='AND'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied
            
            if condition == 'AND':
                # AND logic: All permissions must be present
                for permission_codename in permissions_codename:
                    if not request.user.has_perm(permission_codename):
                        print(f"Permission denied: {permission_codename}")
                        raise PermissionDenied
            elif condition == 'OR':
                # OR logic: At least one permission must be present
                has_any_permission = any(
                    request.user.has_perm(permission_codename)
                    for permission_codename in permissions_codename
                )
                if not has_any_permission:
                    print("Permission denied: User doesn't have any of the required permissions")
                    raise PermissionDenied
            else:
                raise ValueError("Invalid condition: use 'AND' or 'OR'")

            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator