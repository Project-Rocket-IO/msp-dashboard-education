from django.db.models import Sum, Count, Q, F, IntegerField, Avg
from django.db.models.functions import TruncDate, ExtractWeek, ExtractMonth, Cast
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.shortcuts import redirect, render
from django.utils import timezone
from django_tenants.utils import get_tenant

from apps.models import TicketList, TechnicianLabor, get_tickets_worked_on, ProjectList
from apps.access import user_should_land_in_ticket_list

from collections import defaultdict
from datetime import datetime, timedelta
from django.utils import timezone as django_timezone
from json import dumps


class DashboardView(LoginRequiredMixin,TemplateView):
    pass

dashboard_analytics_view = DashboardView.as_view(template_name="dashboards/dashboard-analytics.html")

##################################
##################################
# REAL TIME VIEWS IN USE #########
##################################
##################################

#########
# TICKETS


def prepare_data(tech_labor, tickets, start_date, end_date, time_frame):
    data = []

    labor_hours = get_labor_hours(tech_labor, start_date, end_date)
    open_tickets = tickets.filter(create_date__gte=start_date, create_date__lte=end_date).exclude(status="Closed").count()
    closed_tickets = tickets.filter(create_date__gte=start_date, create_date__lte=end_date, status="Closed").count()
    total_projects = ProjectList.objects.filter(create_date__gte=start_date, create_date__lte=end_date).count()

    data.append({
        # "date": date.strftime("%Y-%m-%d") if time_frame != 'monthly' else date.strftime("%B %Y"),
        "labor_hours": round(labor_hours, 2),
        "open_tickets": open_tickets,
        "closed_tickets": closed_tickets,
        "total_projects": total_projects
    })

    return data


@login_required
def dashboard_analytics_view(request):
    """
    Render the analytics dashboard view with metrics and charts data.

    This view calculates and prepares data for the analytics dashboard,
    including topbar metrics, heatmap data, and bar chart data for
    different time frames (daily, weekly, monthly, yearly). It retrieves
    all tickets and technician labor records, computes metrics such as
    open and closed tickets, and labor hours for each time frame. The
    prepared data is serialized into JSON format and passed to the
    dashboard template for rendering.

    Args:
        request: The HTTP request object.

    Returns:
        HttpResponse: The rendered analytics dashboard page with context data.
    """
    if user_should_land_in_ticket_list(request.user):
        return redirect("apps:tickets.list")

    today = timezone.now().date()
    last_week = today - timedelta(days=6)
    last_month = today - timedelta(days=30)
    last_year = today - timedelta(days=365)
    last_6m = today - timedelta(days=183)

    tickets = TicketList.objects.all()
    tech_labor = TechnicianLabor.objects.all()

    time_frames = ['daily', 'weekly', 'monthly', 'yearly']
    start_dates = [today, last_week, last_month, last_year]
    time_frames_barchart = ['1w', '1m', '6m', '1y']
    start_dates_barchart = [last_week, last_month, last_6m, last_year]

    topbar_metrics = {}
    charts_data = {}
    barchart_metrics = {}

    # Iterate over time frames and calculate metrics for each time frame
    # Store the results in topbar_metrics and charts_data dictionaries
    for i, time_frame in enumerate(time_frames):
        start_date = start_dates[i]
        end_date = today

        # Calculate the topbar metrics for this time frame
        topbarMetrics = prepare_data(tech_labor, tickets, start_date, end_date, time_frame)
        # Calculate the heatmap data for this time frame
        heatmap = prepare_heatmap_data(tech_labor, start_date, end_date, time_frame)

        # Store the results in the topbar_metrics dictionary
        topbar_metrics[time_frame] = {
            "open_tickets": topbarMetrics[0]["open_tickets"],
            "closed_tickets": topbarMetrics[0]["closed_tickets"],
            "labor_hours": topbarMetrics[0]["labor_hours"], # time posted
            "total_projects": topbarMetrics[0]['total_projects']
        }

        # Store the results in the charts_data dictionary
        charts_data[time_frame] = heatmap


    for i, time_frame in enumerate(time_frames_barchart):
       
        # fetch all tickets that were created in this timeframe
        start_date = start_dates_barchart[i]
        end_date = today


        # Filter tickets created within the timeframe
        tickets = TicketList.objects.filter(
            create_date__gte=start_date,
            create_date__lte=end_date
        ).filter(
            technician_labor__created_at__date__gte=start_date,  # Convert techlabor datetime to date when filtering to prevent unexpected behavior
            technician_labor__created_at__date__lte=end_date,    # Convert techlabor datetime to date when filtering to prevent unexpected behavior
            # technician_labor__is_tracked=True # TODO: check if this is needed
        ).distinct()  # Use distinct to ensure each ticket is counted only once

        # Count tickets that have been worked on within the timeframe
        total_tickets = tickets.count()


        # Calculate total hours worked within the timeframe for these tickets
        tech_labor_records = TechnicianLabor.objects.filter(
            ticket__in=tickets,
            created_at__date__gte=start_date, # Convert datetime to date when filtering to prevent unexpected behavior
            created_at__date__lte=end_date    # Convert datetime to date when filtering to prevent unexpected behavior
            # is_tracked=True # TODO: check if this is needed
        )
        total_minutes_committed = tech_labor_records.aggregate(total_minutes=Sum('minutes'))['total_minutes'] or 0
        hours_committed = total_minutes_committed / 60  # converting minutes to hours

        # Calculate average session duration for tickets worked on in this timeframe
        avg_minutes = tech_labor_records.aggregate(avg_minutes=Avg('minutes'))['avg_minutes'] or 0
        avg_hours, avg_minutes_remaining = divmod(avg_minutes, 60)
        avg_session_duration = f"{int(avg_hours)} {int(avg_minutes_remaining)}"


        barchartMetrics = {
            'totalTickets': total_tickets, # total tickets worked on this timeframe (that was also created in that timeframe)
            'hoursCommitted': int(hours_committed), # total hours worked on this timeframe (on tickets that was also created in that timeframe)
            'avgSessionDuration': avg_session_duration # average time worked on in this timeframe (on tickets that was also created in that timeframe)
        }

        # Store the barchart metrics in the barchart_metrics dictionary
        barchart_metrics[time_frame] = barchartMetrics

    # Get the current tenant's company name
    try:
        tenant = getattr(request, 'tenant', None)
        company_name = tenant.company_name if tenant else "Project Rocket"
    except:
        company_name = "Project Rocket"
    
    # Create the context dictionary to pass to the template
    context = {
        "charts_data": dumps(charts_data),
        "topbar_metrics": dumps(topbar_metrics),
        "barchart_metrics": dumps(barchart_metrics),
        "tickets_worked_on": get_tickets_worked_on(),
        "company_name": company_name
    }

    # Render the template with the context data
    return render(request, 'dashboards/dashboard-analytics.html', context)

# Heatmap functions
def prepare_heatmap_data_weekly(tech_labor, start_date, end_date):
    # For daily and weekly views, we need detailed hourly data
    labor_data = tech_labor.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).values(
        'ticket',
        'created_at__date',
        'ticket__status'
    ).annotate(
        hours=Cast(F('minutes') / 60, IntegerField()) + 1
    )

    data = defaultdict(lambda: {
        'date': None,
        'hours': {hour: {'tickets': 0} for hour in range(1, 19)}  # Pre-fill hours 1 to 18
    })

    for entry in labor_data:
        date = entry['created_at__date'].strftime('%Y-%m-%d')
        hours = entry['hours']

        # Start filling in data
        data[date]['date'] = date
        data[date]['hours'][hours]['tickets'] += 1
        
   
    count = len(data)
    # only for weekly view
    if count < 7:
        # Ensure the entire week is filled regardless of data
        start_date = django_timezone.now() - timedelta(days=6) 

        # Loop through the entire week (7 days)
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            date = current_date.strftime("%Y-%m-%d")
            data[date]['date'] = date

    return list(data.values())

def prepare_heatmap_data_daily(tech_labor, start_date, end_date):
    labor_data = tech_labor.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).values(
        'ticket',
        'created_at__date',
        'ticket__status'
    ).annotate(
        hours=Cast(F('minutes') / 60, IntegerField()) + 1
    )

    data = defaultdict(lambda: {
        'date': None,
        'hours': {hour: {'tickets': 0} for hour in range(1, 19)}  # Pre-fill hours 1 to 18
    })
    count = labor_data.count()

    if count < 1:
        print('only in daily view')
        print(start_date, end_date)
        # It should only be for daily view
        date = django_timezone.now().strftime("%Y-%m-%d")
        data[date]['date'] = date
        return list(data.values())


    for entry in labor_data:
        date = entry['created_at__date'].strftime('%Y-%m-%d')
        hours = entry['hours']

        # Start filling in data
        data[date]['date'] = date
        data[date]['hours'][hours]['tickets'] += 1        
    
    return list(data.values())

def prepare_heatmap_data_monthly(tech_labor, start_date, end_date):
                
    labor_data = tech_labor.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).annotate(
        date=TruncDate('created_at')
    ).values(
        'date'
    ).annotate(
        count=Count('id')  # Count unique 'id' per date
    ).order_by('date')

    formatted_data = []

    data_dict = defaultdict(lambda: 0)

    # Fill the dictionary with actual labor_data counts
    for value in labor_data:
        data_dict[value['date'].strftime('%Y-%m-%d')] = value['count']

    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        formatted_data.append({
            'date': date_str,
            'count': data_dict[date_str]  # Will be 0 if the date is missing
        })
        current_date += timedelta(days=1)

    # Print or return the formatted_data
    return formatted_data

def prepare_heatmap_data_yearly(tech_labor, start_date, end_date):
    # Aggregate data by month and week
    labor_data = tech_labor.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).annotate(
        month=ExtractMonth('created_at'),  # Extract month number
        week=ExtractWeek('created_at')  # Extract week number
    ).values(
        'month', 'week'
    ).annotate(
        count=Count('id')  # Count unique 'id' per month and week
    ).order_by('month', 'week')


    # Prepare the heatmap data structure
    heatmap_data = defaultdict(lambda: [0] * 5)  # 12 rows (months) and 5 columns (weeks)
    
    for value in labor_data:
        month = value['month']
        week = value['week'] - 1  # Adjusting week index to 0-based
        if week%4 > 4:  # Cap the week to 5th column
            week = 4
        heatmap_data[month - 1][week%5] += value['count']  # month-1 for 0-based indexing in heatmap

    # Format data as a list of lists for heatmap
    formatted_data = []
    for month in range(12):
        formatted_data.append({
            'month': month + 1,
            'weeks': heatmap_data[month]  # Counts for each week
        })

    return formatted_data

def prepare_heatmap_data(tech_labor, start_date, end_date, time_frame):
    if time_frame == 'yearly':
        return prepare_heatmap_data_yearly(tech_labor, start_date, end_date)
    elif time_frame == 'monthly':
        return prepare_heatmap_data_monthly(tech_labor, start_date, end_date)
    elif time_frame == 'weekly':
        return prepare_heatmap_data_weekly(tech_labor, start_date, end_date)
    else:
        return prepare_heatmap_data_daily(tech_labor, start_date, end_date)


def get_labor_hours(tech_labor, start_date, end_date):
    """
    Calculate the total labor hours for a given date range.

    This function filters the TechnicianLabor records based on the 
    provided start and end dates, aggregates the total minutes worked, 
    and converts it to hours.

    Args:
        tech_labor: A QuerySet of TechnicianLabor objects.
        start_date: A date object representing the start of the range.
        end_date: A date object representing the end of the range.

    Returns:
        A float representing the total labor hours within the specified date range.
        Returns 0 if no labor data is found in the range.
    """
    filters = Q(created_at__date__gte=start_date) & Q(created_at__date__lte=end_date)
    labor_hours = tech_labor.filter(filters).aggregate(total_hours=Sum('minutes'))['total_hours']
    return labor_hours / 60 if labor_hours else 0
