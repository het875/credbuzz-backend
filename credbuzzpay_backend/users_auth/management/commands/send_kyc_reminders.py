"""
Management Command: Send KYC Pending Reminders
==============================================
Sends reminder emails to users who have not completed their KYC within 24 hours.

Usage:
    python manage.py send_kyc_reminders

Can be scheduled via cron or Celery for automated execution.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from users_auth.models import User
from kyc_verification.models import KYCApplication, MegaStep
from users_auth.email_service import send_kyc_pending_reminder_email
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send KYC pending reminder emails to users who registered 24+ hours ago but have not completed KYC'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Hours since registration to send reminder (default: 24)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run - show who would receive emails without sending',
        )

    def handle(self, *args, **options):
        hours_threshold = options['hours']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS(f'\nStarting KYC reminder job...'))
        self.stdout.write(f'Looking for users registered {hours_threshold}+ hours ago with incomplete KYC\n')
        
        # Calculate cutoff time
        cutoff_time = timezone.now() - timedelta(hours=hours_threshold)
        
        # Find users who:
        # 1. Registered before cutoff time
        # 2. Have KYC application
        # 3. KYC is not completed (current_step > 1 but mega_step != COMPLETED)
        # 4. Haven't been sent a reminder in the last 24 hours
        
        eligible_users = []
        
        kyc_apps = KYCApplication.objects.filter(
            user__created_at__lte=cutoff_time,
            current_step__gt=1,  # Started KYC
            mega_step__in=[MegaStep.IDENTITY_PROOF, MegaStep.SELFIE_AND_BUSINESS]  # Not completed
        ).select_related('user')
        
        self.stdout.write(f'Found {kyc_apps.count()} KYC applications in progress\n')
        
        sent_count = 0
        failed_count = 0
        skipped_count = 0
        
        for kyc_app in kyc_apps:
            user = kyc_app.user
            current_step = kyc_app.current_step
            
            # Check if we've sent a reminder recently (optional - implement if you add a last_reminder_sent field)
            # For now, we'll send to all eligible users
            
            eligible_users.append({
                'user': user,
                'email': user.email,
                'name': user.get_full_name() or user.username,
                'current_step': current_step,
                'registered': user.created_at,
            })
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN MODE - NO EMAILS WILL BE SENT ===\n'))
        
        self.stdout.write(f'\nProcessing {len(eligible_users)} users:\n')
        
        for user_data in eligible_users:
            user = user_data['user']
            email = user_data['email']
            name = user_data['name']
            current_step = user_data['current_step']
            
            self.stdout.write(
                f'  • {name} ({email}) - Step {current_step}/7'
            )
            
            if dry_run:
                self.stdout.write(self.style.WARNING('    [DRY RUN - Would send email]'))
                continue
            
            # Send reminder email
            try:
                email_sent = send_kyc_pending_reminder_email(
                    email=email,
                    user_name=name,
                    current_step=current_step,
                    total_steps=7
                )
                
                if email_sent:
                    sent_count += 1
                    self.stdout.write(self.style.SUCCESS('    ✓ Sent successfully'))
                else:
                    failed_count += 1
                    self.stdout.write(self.style.ERROR('    ✗ Failed to send'))
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f'    ✗ Error: {str(e)}'))
                logger.error(f'Failed to send KYC reminder to {email}: {str(e)}')
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('\nKYC Reminder Job Complete!\n'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN - {len(eligible_users)} emails would be sent'))
        else:
            self.stdout.write(f'Total Eligible: {len(eligible_users)}')
            self.stdout.write(self.style.SUCCESS(f'✓ Sent: {sent_count}'))
            if failed_count > 0:
                self.stdout.write(self.style.ERROR(f'✗ Failed: {failed_count}'))
            if skipped_count > 0:
                self.stdout.write(self.style.WARNING(f'⊘ Skipped: {skipped_count}'))
        
        self.stdout.write('=' * 60 + '\n')
