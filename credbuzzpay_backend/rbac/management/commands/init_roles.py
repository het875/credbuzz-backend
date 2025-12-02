"""
Management command to initialize default roles for the RBAC system.
Creates the 5 default user roles with their hierarchy.
"""

from django.core.management.base import BaseCommand
from rbac.models import UserRole, RoleHierarchy, RoleLevel


class Command(BaseCommand):
    help = 'Initialize default user roles and role hierarchy for RBAC system'
    
    def handle(self, *args, **options):
        self.stdout.write('Initializing default user roles...')
        
        # Define default roles with their hierarchy levels
        default_roles = [
            {
                'name': 'Developer',
                'code': 'DEVELOPER',
                'description': 'Full project and all access. Has complete control over the entire system including development, deployment, and all administrative functions.',
                'level': RoleLevel.DEVELOPER,
                'is_system_role': True
            },
            {
                'name': 'Super Admin',
                'code': 'SUPER_ADMIN',
                'description': 'Full access to all administrative functions. Can manage all roles, apps, features, and users except developer-level operations.',
                'level': RoleLevel.SUPER_ADMIN,
                'is_system_role': True
            },
            {
                'name': 'Admin',
                'code': 'ADMIN',
                'description': 'Limited app and feature access as assigned by Super Admin. Can manage clients and end users within assigned scope.',
                'level': RoleLevel.ADMIN,
                'is_system_role': True
            },
            {
                'name': 'Client',
                'code': 'CLIENT',
                'description': 'Portal apps and features access as given by Admin. Can manage end users within their scope.',
                'level': RoleLevel.CLIENT,
                'is_system_role': True
            },
            {
                'name': 'End User',
                'code': 'END_USER',
                'description': 'Limited access as given by Clients. Basic access to assigned features only.',
                'level': RoleLevel.END_USER,
                'is_system_role': True
            }
        ]
        
        created_roles = {}
        
        for role_data in default_roles:
            role, created = UserRole.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'code': role_data['code'],
                    'description': role_data['description'],
                    'level': role_data['level'],
                    'is_system_role': role_data['is_system_role'],
                    'is_active': True
                }
            )
            created_roles[role_data['name']] = role
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created role: {role.name} (Level {role.level})'))
            else:
                self.stdout.write(self.style.WARNING(f'  Role already exists: {role.name}'))
        
        # Create role hierarchy relationships
        self.stdout.write('\nSetting up role hierarchy...')
        
        hierarchy_relationships = [
            ('Developer', 'Super Admin'),
            ('Super Admin', 'Admin'),
            ('Admin', 'Client'),
            ('Client', 'End User')
        ]
        
        for parent_name, child_name in hierarchy_relationships:
            parent_role = created_roles.get(parent_name)
            child_role = created_roles.get(child_name)
            
            if parent_role and child_role:
                hierarchy, created = RoleHierarchy.objects.get_or_create(
                    parent_role=parent_role,
                    child_role=child_role
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  {parent_name} -> {child_name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'  Hierarchy already exists: {parent_name} -> {child_name}'))
        
        self.stdout.write(self.style.SUCCESS('\nDefault roles initialization complete!'))
        self.stdout.write(f'\nRole Hierarchy:')
        self.stdout.write('  Level 1: Developer (Full Access)')
        self.stdout.write('  Level 2: Super Admin (Full Admin Access)')
        self.stdout.write('  Level 3: Admin (Limited App/Feature Access)')
        self.stdout.write('  Level 4: Client (Portal Access)')
        self.stdout.write('  Level 5: End User (Basic Access)')
