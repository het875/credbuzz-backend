"""
Django management command to create master superadmin
Usage: python manage.py create_master_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from erp.models import Branch, UserPlatformAccess, AppAccessControl, AppFeature
import getpass

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a master superadmin user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Master admin email address',
        )
        parser.add_argument(
            '--mobile',
            type=str,
            help='Master admin mobile number',
        )
        parser.add_argument(
            '--first_name',
            type=str,
            help='Master admin first name',
        )
        parser.add_argument(
            '--last_name',
            type=str,
            help='Master admin last name',
        )

    def handle(self, *args, **options):
        """Create master superadmin."""
        
        # Check if master superadmin already exists
        if User.objects.filter(role='master_superadmin').exists():
            self.stdout.write(
                self.style.WARNING('Master superadmin already exists!')
            )
            return

        # Get user input
        email = options.get('email') or input('Email address: ')
        mobile = options.get('mobile') or input('Mobile number: ')
        first_name = options.get('first_name') or input('First name: ')
        last_name = options.get('last_name') or input('Last name: ')
        
        # Validate required fields
        if not all([email, mobile, first_name, last_name]):
            self.stdout.write(
                self.style.ERROR('All fields are required!')
            )
            return

        # Get password
        password = getpass.getpass('Password: ')
        password_confirm = getpass.getpass('Confirm password: ')
        
        if password != password_confirm:
            self.stdout.write(
                self.style.ERROR('Passwords do not match!')
            )
            return

        if len(password) < 8:
            self.stdout.write(
                self.style.ERROR('Password must be at least 8 characters!')
            )
            return

        try:
            with transaction.atomic():
                # Get main branch
                main_branch = Branch.objects.filter(branch_code='MAIN001').first()
                if not main_branch:
                    self.stdout.write(
                        self.style.ERROR('Main branch not found! Please run migrations first.')
                    )
                    return

                # Create master superadmin
                user = User.objects.create_user(
                    email=email,
                    mobile=mobile,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                    role='master_superadmin',
                    branch=main_branch,
                    is_active=True,
                    is_staff=True,
                    is_superuser=True,
                    is_email_verified=True,
                    is_mobile_verified=True
                )

                # Grant all platform access
                platforms = ['web', 'mobile_app', 'admin_panel', 'api']
                for platform in platforms:
                    UserPlatformAccess.objects.create(
                        user=user,
                        platform=platform,
                        is_allowed=True,
                        granted_by=user
                    )

                # Grant all feature access
                features = AppFeature.objects.filter(is_active=True)
                for feature in features:
                    AppAccessControl.objects.create(
                        user=user,
                        feature=feature,
                        is_allowed=True,
                        granted_by=user
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Master superadmin created successfully!\n'
                        f'User ID: {user.id}\n'
                        f'Email: {user.email}\n'
                        f'Mobile: {user.mobile}\n'
                        f'Role: {user.role}\n'
                        f'Branch: {user.branch.branch_name}'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating master superadmin: {str(e)}')
            )
            return