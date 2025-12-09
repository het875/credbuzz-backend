"""
Management command to create a Developer user.

This is the first command to run when setting up the system.
Developer is the highest privileged role and can create Super Admins.

Usage:
    python manage.py create_developer

The command will prompt for:
    - Email
    - Username
    - Password
    - First Name
    - Last Name
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from users_auth.models import User, RoleName
from rbac.models import UserRole, UserRoleAssignment
import getpass
import re


class Command(BaseCommand):
    help = 'Create a Developer user (highest privilege role)'
    
    def add_arguments(self, parser):
        # Optional arguments to skip interactive prompts
        parser.add_argument(
            '--email',
            type=str,
            help='Developer email address',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Developer username',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Developer password (not recommended for security)',
        )
        parser.add_argument(
            '--first-name',
            type=str,
            help='Developer first name',
        )
        parser.add_argument(
            '--last-name',
            type=str,
            help='Developer last name',
        )
        parser.add_argument(
            '--noinput',
            action='store_true',
            help='Skip confirmation prompts',
        )
    
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        return True, "Password is valid"
    
    def get_input(self, prompt, required=True, password=False, validator=None):
        """Get input from user with optional validation"""
        while True:
            if password:
                value = getpass.getpass(prompt)
            else:
                value = input(prompt)
            
            if not value and required:
                self.stdout.write(self.style.ERROR('This field is required.'))
                continue
            
            if validator:
                is_valid, message = validator(value) if callable(validator) else (validator(value), "Invalid input")
                if not is_valid:
                    self.stdout.write(self.style.ERROR(message if isinstance(message, str) else "Invalid input"))
                    continue
            
            return value
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n' + '='*60))
        self.stdout.write(self.style.WARNING('   CREDBUZZ - DEVELOPER USER CREATION'))
        self.stdout.write(self.style.WARNING('='*60))
        self.stdout.write(self.style.NOTICE('''
Developer is the HIGHEST privilege role in the system.
A Developer can:
  - Access entire system including code and configurations
  - Create Super Admins and all other roles
  - Manage all applications and features
  - View all audit logs

⚠️  Keep these credentials secure!
'''))
        
        # Check if Developer role exists
        try:
            developer_role = UserRole.objects.get(code='DEVELOPER')
        except UserRole.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                '\nDeveloper role not found! Run "python manage.py init_roles" first.\n'
            ))
            return
        
        # Get email
        email = options.get('email')
        if not email:
            while True:
                email = self.get_input('Enter Email: ')
                if not self.validate_email(email):
                    self.stdout.write(self.style.ERROR('Invalid email format.'))
                    continue
                if User.objects.filter(email=email).exists():
                    self.stdout.write(self.style.ERROR('Email already exists.'))
                    continue
                break
        else:
            if not self.validate_email(email):
                raise CommandError('Invalid email format.')
            if User.objects.filter(email=email).exists():
                raise CommandError('Email already exists.')
        
        # Get username
        username = options.get('username')
        if not username:
            while True:
                username = self.get_input('Enter Username: ')
                if User.objects.filter(username=username).exists():
                    self.stdout.write(self.style.ERROR('Username already exists.'))
                    continue
                break
        else:
            if User.objects.filter(username=username).exists():
                raise CommandError('Username already exists.')
        
        # Get password
        password = options.get('password')
        if not password:
            while True:
                password = self.get_input('Enter Password: ', password=True)
                is_valid, message = self.validate_password(password)
                if not is_valid:
                    self.stdout.write(self.style.ERROR(message))
                    continue
                
                confirm_password = self.get_input('Confirm Password: ', password=True)
                if password != confirm_password:
                    self.stdout.write(self.style.ERROR('Passwords do not match.'))
                    continue
                break
        else:
            is_valid, message = self.validate_password(password)
            if not is_valid:
                raise CommandError(message)
        
        # Get first name
        first_name = options.get('first_name')
        if not first_name:
            first_name = self.get_input('Enter First Name: ', required=False) or 'System'
        
        # Get last name
        last_name = options.get('last_name')
        if not last_name:
            last_name = self.get_input('Enter Last Name: ', required=False) or 'Developer'
        
        # Confirmation
        if not options.get('noinput'):
            self.stdout.write('\n' + '-'*40)
            self.stdout.write(f'Email:      {email}')
            self.stdout.write(f'Username:   {username}')
            self.stdout.write(f'Name:       {first_name} {last_name}')
            self.stdout.write(f'Role:       Developer (Level 1)')
            self.stdout.write('-'*40 + '\n')
            
            confirm = input('Create this Developer user? [y/N]: ').lower()
            if confirm != 'y':
                self.stdout.write(self.style.WARNING('Cancelled.'))
                return
        
        # Create user
        try:
            with transaction.atomic():
                # Create user
                user = User(
                    email=email,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    user_role=RoleName.DEVELOPER,
                    is_verified=True,
                )
                user.set_password(password)
                user.save()
                
                # Assign Developer role
                UserRoleAssignment.objects.create(
                    user=user,
                    role=developer_role,
                    is_primary=True,
                    assigned_by=user
                )
                
                self.stdout.write(self.style.SUCCESS('\n' + '='*60))
                self.stdout.write(self.style.SUCCESS('   ✅ DEVELOPER USER CREATED SUCCESSFULLY!'))
                self.stdout.write(self.style.SUCCESS('='*60))
                self.stdout.write(self.style.SUCCESS(f'''
   User Code:  {user.user_code}
   Email:      {user.email}
   Username:   {user.username}
   Role:       Developer

   You can now login and create Super Admin users.
'''))
                
        except Exception as e:
            raise CommandError(f'Error creating user: {str(e)}')
