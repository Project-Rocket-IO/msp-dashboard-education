from django.contrib.auth.models import Group

class RBACMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.user_groups = request.user.groups.all()
            request.user_permissions = request.user.get_all_permissions()
        
        response = self.get_response(request)
        return response
