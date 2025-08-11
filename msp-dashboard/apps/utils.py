import os
import re
from django.conf import settings
from django_tenants.utils import get_tenant


def sanitize_filename(filename):
    """
    Sanitize filename to be safe for filesystem
    Replace spaces with underscores and remove special characters
    """
    # Remove or replace problematic characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    return filename


def get_tenant_company_name():
    """
    Get the current tenant's company name
    """
    try:
        tenant = get_tenant()
        return sanitize_filename(tenant.company_name)
    except:
        return "public"


def tenant_ticket_directory_path(instance, filename):
    """
    Upload path for ticket files: ./media/<company_name>/tickets/<ticket_name>/<filename>
    """
    company_name = get_tenant_company_name()
    ticket_name = sanitize_filename(instance.name)
    return f"{company_name}/tickets/{ticket_name}/{filename}"


def tenant_ticket_files_directory_path(instance, filename):
    """
    Upload path for ticket file attachments: ./media/<company_name>/tickets/<ticket_name>/<filename>
    """
    company_name = get_tenant_company_name()
    ticket_name = sanitize_filename(instance.ticket.name)
    return f"{company_name}/tickets/{ticket_name}/{filename}"


def tenant_project_directory_path(instance, filename):
    """
    Upload path for project files: ./media/<company_name>/projects/<project_name>/<filename>
    """
    company_name = get_tenant_company_name()
    project_name = sanitize_filename(instance.name)
    return f"{company_name}/projects/{project_name}/{filename}"


def tenant_project_files_directory_path(instance, filename):
    """
    Upload path for project file attachments: ./media/<company_name>/projects/<project_name>/<filename>
    """
    company_name = get_tenant_company_name()
    project_name = sanitize_filename(instance.project.name)
    return f"{company_name}/projects/{project_name}/{filename}"


def tenant_client_directory_path(instance, filename):
    """
    Upload path for client files: ./media/<company_name>/clients/<client_name>/<filename>
    """
    company_name = get_tenant_company_name()
    client_name = sanitize_filename(instance.name)
    return f"{company_name}/clients/{client_name}/{filename}"


def tenant_client_files_directory_path(instance, filename):
    """
    Upload path for client file attachments: ./media/<company_name>/clients/<client_name>/<filename>
    """
    company_name = get_tenant_company_name()
    client_name = sanitize_filename(instance.client.name)
    return f"{company_name}/clients/{client_name}/{filename}"


def tenant_lead_directory_path(instance, filename):
    """
    Upload path for lead files: ./media/<company_name>/leads/<lead_name>/<filename>
    """
    company_name = get_tenant_company_name()
    lead_name = sanitize_filename(instance.name)
    return f"{company_name}/leads/{lead_name}/{filename}"


def tenant_lead_files_directory_path(instance, filename):
    """
    Upload path for lead file attachments: ./media/<company_name>/leads/<lead_name>/<filename>
    """
    company_name = get_tenant_company_name()
    lead_name = sanitize_filename(instance.lead.name)
    return f"{company_name}/leads/{lead_name}/{filename}"


def tenant_sales_directory_path(instance, filename):
    """
    Upload path for sales files: ./media/<company_name>/sales/<sales_name>/<filename>
    """
    company_name = get_tenant_company_name()
    sales_name = sanitize_filename(instance.name)
    return f"{company_name}/sales/{sales_name}/{filename}"


def create_tenant_directories():
    """
    Create the base directory structure for the current tenant
    """
    company_name = get_tenant_company_name()
    base_path = os.path.join(settings.MEDIA_ROOT, company_name)
    
    # Create main company directory
    os.makedirs(base_path, exist_ok=True)
    
    # Create subdirectories for each entity type
    subdirs = ['tickets', 'projects', 'clients', 'leads', 'sales']
    for subdir in subdirs:
        os.makedirs(os.path.join(base_path, subdir), exist_ok=True)
    
    return base_path 