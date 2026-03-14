from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from apps.models import TicketList, TechnicianUser
from apps.forms import TechnicianLaborAddForm
from apps.access import get_visible_tickets_queryset, user_has_end_user_role

@login_required
def apps_technician_labor_view(request, pk):
    if user_has_end_user_role(request.user):
        raise PermissionDenied

    ticket = get_object_or_404(get_visible_tickets_queryset(request.user), pk=pk)
    technicians = TechnicianUser.objects.all()
    current_user = request.user

    context = {
        "tickets": ticket,
        "technicians": technicians,
        "current_user": current_user,
    }

    if request.method == "POST":
        hours = request.POST.get("hours", 0) or 0
        minutes = request.POST.get("minutes", 0) or 0
        minutes = (int(hours) * 60) + int(minutes)
        if minutes == 0:
            messages.error(request, "Minutes cannot be None")
            return redirect(reverse("apps:tickets.details", kwargs={"pk": ticket.pk}))

        copyrequest = request.POST.copy()
        copyrequest['minutes'] = minutes

        form = TechnicianLaborAddForm(
            copyrequest or None,
            request.FILES or None,
            initial={"created_by": current_user},
        )
        if form.is_valid():
            obj = form.save(commit=False)
            obj.ticket = ticket
            obj.submitted_by = current_user
            obj.save()
            messages.success(request, "Time Posted Successfully!")
            # return redirect("apps:tickets.list")
            return redirect(reverse("apps:tickets.details", kwargs={"pk": ticket.pk}))
        else:
            print(form.errors)
            messages.error(request, "Something went wrong!")
            return redirect(reverse("apps:tickets.details", kwargs={"pk": ticket.pk}))
    return render(request, "apps/support-tickets/apps-tickets-details.html", context)


