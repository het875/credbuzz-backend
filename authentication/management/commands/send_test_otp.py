"""
Management command to test OTP email sending.
Usage: python manage.py send_test_otp --email user@example.com
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from authentication.utils import send_otp_email

User = get_user_model()


class Command(BaseCommand):
    help = 'Send a test OTP email to a user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send OTP to',
            required=True
        )
        parser.add_argument(
            '--type',
            type=str,
            default='email_verification',
            choices=['email_verification', 'password_reset', 'login_verification'],
            help='Type of OTP email to send'
        )
        parser.add_argument(
            '--create-user',
            action='store_true',
            help='Create a test user if the email does not exist'
        )

    def handle(self, *args, **options):
        email = options['email']
        otp_type = options['type']
        create_user = options['create_user']

        self.stdout.write(f'Attempting to send {otp_type} OTP to: {email}')

        # Try to find user
        try:
            user = User.objects.get(email=email, is_active=True)
            self.stdout.write(f'Found user: {user.id} - {user.email}')
        except User.DoesNotExist:
            if create_user:
                # Create a test user
                self.stdout.write('Creating test user...')
                user = User.objects.create_user(
                    email=email,
                    password='TestPassword123',
                    first_name='Test',
                    last_name='User'
                )
                self.stdout.write(f'Created test user: {user.id} - {user.email}')
            else:
                raise CommandError(f'User with email {email} does not exist. Use --create-user to create one.')

        # Send OTP email
        try:
            success, otp, message = send_otp_email(user, otp_type)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ OTP email sent successfully!')
                )
                self.stdout.write(f'OTP: {otp}')
                self.stdout.write(f'Message: {message}')
                
                # Show OTP saved in database
                user.refresh_from_db()
                self.stdout.write(f'OTP saved in DB: {user.email_otp}')
                self.stdout.write(f'OTP timestamp: {user.email_otp_updated_at}')
                
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to send OTP email: {message}')
                )
                
        except Exception as e:
            raise CommandError(f'Error sending OTP: {str(e)}')
            
        self.stdout.write('Test completed.')