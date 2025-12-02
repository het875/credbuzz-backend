"""
Management command to create a Super Admin user.

This command requires a Developer account to run.
The Developer must provide their credentials to authorize the creation.

Usage:
    python manage.py create_superadmin

The command will prompt for:
    - Developer email (for authorization)
    - Developer password (for authorization)
    - Super Admin details
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from users_auth.models import User, RoleName
from rbac.models import UserRole, UserRoleAssignment
import getpass
import re


class Command(BaseCommand):
    help = 'Create a Super Admin user (requires Developer authorization)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dev-email',
            type=str,
            help='Developer email for authorization',
        )
        parser.add_argument(
            '--dev-password',
            type=str,
            help='Developer password for authorization (use with --noinput)',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Super Admin email address',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Super Admin username',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Super Admin password',
        )
        parser.add_argument(
            '--first-name',
            type=str,
            help='Super Admin first name',
        )
        parser.add_argument(
            '--last-name',
            type=str,
            help='Super Admin last name',
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
    
    def get_input(self, prompt, required=True, password=False):
        """Get input from user"""
        while True:
            if password:
                value = getpass.getpass(prompt)
            else:
                value = input(prompt)
            
            if not value and required:
                self.stdout.write(self.style.ERROR('This field is required.'))
                continue
            
            return value
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n' + '='*60))
        self.stdout.write(self.style.WARNING('   CREDBUZZ - SUPER ADMIN USER CREATION'))
        self.stdout.write(self.style.WARNING('='*60))
        self.stdout.write(self.style.NOTICE('''
Super Admin is a high privilege role in the system.
A Super Admin can:
  - Full access to all applications
  - Create and manage Admins, Clients, End Users
  - Assign permissions and roles
  - View audit logs

🔐 Developer authorization required to create Super Admin.
'''))
        
        # Check if Super Admin role exists
        try:
            superadmin_role = UserRole.objects.get(code='SUPER_ADMIN')
        except UserRole.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                '\nSuper Admin role not found! Run "python manage.py init_roles" first.\n'
            ))
            return
        
        # Authorize with Developer credentials
        self.stdout.write(self.style.WARNING('\n--- Developer Authorization ---'))
        
        dev_email = options.get('dev_email')
        if not dev_email:
            dev_email = self.get_input('Developer Email: ')
        
        dev_password = options.get('dev_password')
        if not dev_password:
            dev_password = self.get_input('Developer Password: ', password=True)
        
        # Verify developer
        try:
            developer = User.objects.get(email=dev_email)
            if not developer.check_password(dev_password):
                raise CommandError('Invalid developer credentials.')
            if developer.user_role != RoleName.DEVELOPER:
                raise CommandError('This user is not a Developer.')
        except User.DoesNotExist:
            raise CommandError('Developer not found.')
        
        self.stdout.write(self.style.SUCCESS(f'✓ Authorized as: {developer.full_name}'))
        
        # Get Super Admin details
        self.stdout.write(self.style.WARNING('\n--- Super Admin Details ---'))
        
        # Get email
        email = options.get('email')
        if not email:
            while True:
                email = self.get_input('Super Admin Email: ')
                if not self.validate_email(email):
                    self.stdout.write(self.style.ERROR('Invalid email format.'))
                    continue
                if User.objects.filter(email=email).exists():
                    self.stdout.write(self.style.ERROR('Email already exists.'))
                    continue
                break
        
        # Get username
        username = options.get('username')
        if not username:
            while True:
                username = self.get_input('Super Admin Username: ')
                if User.objects.filter(username=username).exists():
                    self.stdout.write(self.style.ERROR('Username already exists.'))
                    continue
                break
        
        # Get password
        password = options.get('password')
        if not password:
            while True:
                password = self.get_input('Super Admin Password: ', password=True)
                is_valid, message = self.validate_password(password)
                if not is_valid:
                    self.stdout.write(self.style.ERROR(message))
                    continue
                
                confirm_password = self.get_input('Confirm Password: ', password=True)
                if password != confirm_password:
                    self.stdout.write(self.style.ERROR('Passwords do not match.'))
                    continue
                break
        
        # Get first name
        first_name = options.get('first_name')
        if not first_name:
            first_name = self.get_input('First Name: ', required=False) or 'Super'
        
        # Get last name
        last_name = options.get('last_name')
        if not last_name:
            last_name = self.get_input('Last Name: ', required=False) or 'Admin'
        
        # Confirmation
        if not options.get('noinput'):
            self.stdout.write('\n' + '-'*40)
            self.stdout.write(f'Email:      {email}')
            self.stdout.write(f'Username:   {username}')
            self.stdout.write(f'Name:       {first_name} {last_name}')
            self.stdout.write(f'Role:       Super Admin (Level 2)')
            self.stdout.write(f'Created By: {developer.email}')
            self.stdout.write('-'*40 + '\n')
            
            confirm = input('Create this Super Admin user? [y/N]: ').lower()
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
                    user_role=RoleName.SUPER_ADMIN,
                    is_verified=True,
                )
                user.set_password(password)
                user.save()
                
                # Assign Super Admin role
                UserRoleAssignment.objects.create(
                    user=user,
                    role=superadmin_role,
                    is_primary=True,
                    assigned_by=developer
                )
                
                self.stdout.write(self.style.SUCCESS('\n' + '='*60))
                self.stdout.write(self.style.SUCCESS('   ✅ SUPER ADMIN USER CREATED SUCCESSFULLY!'))
                self.stdout.write(self.style.SUCCESS('='*60))
                self.stdout.write(self.style.SUCCESS(f'''
   User Code:  {user.user_code}
   Email:      {user.email}
   Username:   {user.username}
   Role:       Super Admin

   Share these credentials securely with the Super Admin.
'''))
                
        except Exception as e:
            raise CommandError(f'Error creating user: {str(e)}')
