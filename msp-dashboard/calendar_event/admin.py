from django.contrib import admin

from .models import CalendarEvents

# Register your models here.
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'name','location', 'start', 'end', 'creator')

admin.site.register(CalendarEvents,EventAdmin)
