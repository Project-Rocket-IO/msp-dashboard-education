from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from social_django.views import auth as social_auth_view
from social_django.views import complete as social_complete_view


ENTRA_ID_BACKEND = "azuread-oauth2"


@never_cache
def entra_id_begin(request):
    return social_auth_view(request, ENTRA_ID_BACKEND)


@never_cache
@csrf_exempt
def entra_id_callback(request):
    return social_complete_view(request, ENTRA_ID_BACKEND)
