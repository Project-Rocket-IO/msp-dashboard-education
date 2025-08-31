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
    Upload path for ticket files: ./media/<schema>/tickets/<ticket_name>/<filename>
    """
    ticket_name = sanitize_filename(instance.name)
    
    # Always use the current schema for the upload path
    from django.db import connection
    current_schema = connection.settings_dict.get("SCHEMA", "public")
    
    return f"tickets/{ticket_name}/{filename}"


def tenant_ticket_files_directory_path(instance, filename):
    """
    Upload path for ticket file attachments: ./media/<schema>/tickets/<ticket_name>/<filename>
    """
    ticket_name = sanitize_filename(instance.ticket.name)
    
    # Always use the current schema for the upload path
    from django.db import connection
    current_schema = connection.settings_dict.get("SCHEMA", "public")
    
    return f"tickets/{ticket_name}/{filename}"


def tenant_project_directory_path(instance, filename):
    """
    Upload path for project files: ./media/<schema>/projects/<project_name>/<filename>
    """
    project_name = sanitize_filename(instance.name)
    
    # Always use the current schema for the upload path
    from django.db import connection
    current_schema = connection.settings_dict.get("SCHEMA", "public")
    
    return f"projects/{project_name}/{filename}"


def tenant_project_files_directory_path(instance, filename):
    """
    Upload path for project file attachments: ./media/<schema>/projects/<project_name>/<filename>
    """
    project_name = sanitize_filename(instance.project.name)
    
    # Always use the current schema for the upload path
    from django.db import connection
    current_schema = connection.settings_dict.get("SCHEMA", "public")
    
    return f"projects/{project_name}/{filename}"


def tenant_client_directory_path(instance, filename):
    """
    Upload path for client files: ./media/<schema>/clients/<client_name>/<filename>
    """
    client_name = sanitize_filename(instance.name)
    
    # Always use the current schema for the upload path
    from django.db import connection
    current_schema = connection.settings_dict.get("SCHEMA", "public")
    
    return f"clients/{client_name}/{filename}"


def tenant_client_files_directory_path(instance, filename):
    """
    Upload path for client file attachments: ./media/<schema>/clients/<client_name>/<filename>
    """
    client_name = sanitize_filename(instance.client.name)
    
    # Always use the current schema for the upload path
    from django.db import connection
    current_schema = connection.settings_dict.get("SCHEMA", "public")
    
    return f"clients/{client_name}/{filename}"


def tenant_lead_directory_path(instance, filename):
    """
    Upload path for lead files: ./media/<schema>/leads/<lead_name>/<filename>
    """
    lead_name = sanitize_filename(instance.name)
    
    # Always use the current schema for the upload path
    from django.db import connection
    current_schema = connection.settings_dict.get("SCHEMA", "public")
    
    return f"leads/{lead_name}/{filename}"


def tenant_lead_files_directory_path(instance, filename):
    """
    Upload path for lead file attachments: ./media/<schema>/leads/<lead_name>/<filename>
    """
    lead_name = sanitize_filename(instance.lead.name)
    
    # Always use the current schema for the upload path
    from django.db import connection
    current_schema = connection.settings_dict.get("SCHEMA", "public")
    
    return f"leads/{lead_name}/{filename}"


def tenant_sales_directory_path(instance, filename):
    """
    Upload path for sales files: ./media/<schema>/sales/<sales_name>/<filename>
    """
    sales_name = sanitize_filename(instance.name)
    
    # Always use the current schema for the upload path
    from django.db import connection
    current_schema = connection.settings_dict.get("SCHEMA", "public")
    
    return f"sales/{sales_name}/{filename}"


def create_tenant_directories():
    """
    Create the base directory structure for the current tenant
    """
    # Always use the current schema directory (no company name subdirectory)
    from django.db import connection
    current_schema = connection.settings_dict.get("SCHEMA", "public")
    
    # Create subdirectories directly under the schema directory
    subdirs = ['tickets', 'projects', 'clients', 'leads', 'sales']
    for subdir in subdirs:
        subdir_path = os.path.join(settings.MEDIA_ROOT, current_schema, subdir)
        os.makedirs(subdir_path, exist_ok=True)
    
    return os.path.join(settings.MEDIA_ROOT, current_schema) 