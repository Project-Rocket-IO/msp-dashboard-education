from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import Group, Permission
from django.conf import settings
from pathlib import Path
import json

class Command(BaseCommand):
    help = 'Set up groups and permissions from groups.json file'

    def handle(self, *args, **kwargs):
        # Try multiple possible file locations
        possible_paths = [
            settings.BASE_DIR / 'groups.json',
            settings.BASE_DIR / 'src' / 'json' / 'groups.json',
            settings.BASE_DIR / 'static' / 'json' / 'groups.json',
        ]
        
        file_path = None
        for path in possible_paths:
            if path.exists():
                file_path = path
                break
        
        if not file_path:
            self.stdout.write(self.style.ERROR(f'Groups file not found. Tried: {[str(p) for p in possible_paths]}'))
            return
        
        self.stdout.write(f'Using file: {file_path}')
        
        with open(file_path, 'r') as file:
            data = json.load(file)
            
            for item in data:
                group_name = item['fields']['name']
                group, created = Group.objects.get_or_create(name=group_name)
                
                if created:
                    self.stdout.write(f'Created group: {group_name}')
                else:
                    self.stdout.write(f'Group already exists: {group_name}')
                
                permissions = item['fields']['permissions']
                resolved_permissions = []
                
                for perm_data in permissions:
                    try:
                        # Handle the permission format: [codename, app_label, model_name]
                        if isinstance(perm_data, list) and len(perm_data) == 3:
                            codename, app_label, model_name = perm_data
                            permission = Permission.objects.get(
                                codename=codename,
                                content_type__app_label=app_label,
                                content_type__model=model_name
                            )
                            resolved_permissions.append(permission)
                        else:
                            self.stdout.write(self.style.WARNING(f'Invalid permission format: {perm_data}'))
                    except Permission.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'Permission not found: {perm_data}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error adding permission {perm_data}: {e}'))
                
                group.permissions.set(resolved_permissions)
                group.save()
                self.stdout.write(
                    f'Set {len(resolved_permissions)} permissions on {group_name}'
                )

        self.stdout.write(self.style.SUCCESS('Groups and permissions set up successfully!'))

