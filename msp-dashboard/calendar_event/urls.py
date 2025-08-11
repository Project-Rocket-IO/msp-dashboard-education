from django.urls import path, include
from . import views

app_name = 'calendar_event'

urlpatterns = [
    path("", view=views.apps_calendar_view, name="calendar-events"),
    path("delete/", view=views.apps_calendar_view_delete, name="calendar-events-delete"),
    path("<int:pk>/", view=views.apps_calendar_edit_view, name="calendar-events-edit"),
    #  path("event/", views.CalendarEventViewSet.as_view({"post": "create", "get": "list"}),
    #      name = "calendar-events"),
    # path("event/<int:pk>",
    #      views.CalendarEventViewSet.as_view({"get": "retrieve", "patch": "update", "delete": "destroy"}),
    #      name = "calender-event-details"),
]