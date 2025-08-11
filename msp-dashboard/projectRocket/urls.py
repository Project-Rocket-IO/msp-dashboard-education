from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from .views import MyPasswordChangeView, MyPasswordSetView
from django.conf.urls.static import static
from django.conf import settings
from rbac.views import view_home
from two_factor.urls import urlpatterns as tf_urls


urlpatterns = [
    path("admin/", admin.site.urls),
    # Dashboard
    path("", view_home, name="home"),
    # Dashboard
    path("payments/", include("payments.urls", namespace="payments")),
    # Apps
    path("apps/", include("apps.urls")),
    # Calender Events
    path("calendar/", include("calendar_event.urls")),
    # Chat
    path("chat/", include("chat.urls")),
    # Atlas AI Assistant
    path("atlas/", include("atlas.urls")),
    # Layouts
    path("layouts/", include("layouts.urls")),
    # Pages
    path("pages/", include("pages.urls")),
    path(
        "account/password/change/",
        login_required(MyPasswordChangeView.as_view()),
        name="account_change_password",
    ),
    path(
        "account/password/set/",
        login_required(MyPasswordSetView.as_view()),
        name="account_set_password",
    ),
    # All Auth
    path("account/", include("allauth.urls")),
    path("social-auth/", include("social_django.urls", namespace="social")),
    path("", include(tf_urls)),
]

# print(settings.DEBUG)
# if settings.DEBUG:
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# from debug_toolbar.toolbar import debug_toolbar_urls

# urlpatterns += debug_toolbar_urls()
