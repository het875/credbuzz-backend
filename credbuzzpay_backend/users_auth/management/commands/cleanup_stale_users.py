"""
Management command to cleanup stale unverified users.

Stale users are those who:
1. Registered but never verified their email (is_email_verified=False)
2. Account is older than a specified number of days

Usage:
    # Dry run - see what would be deleted
    python manage.py cleanup_stale_users --days=7 --dry-run
    
    # Actually delete stale users
    python manage.py cleanup_stale_users --days=7
    
    # With verbose output
    python manage.py cleanup_stale_users --days=7 -v 2

This command can be scheduled via cron:
    0 2 * * * cd /path/to/project && python manage.py cleanup_stale_users --days=7
"""

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from users_auth.models import User, UserActivityLog


class Command(BaseCommand):
    help = 'Cleanup stale unverified users who never completed email verification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Delete users who registered more than this many days ago (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of users to delete per batch (default: 100)'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        verbosity = options['verbosity']

        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)

        self.stdout.write(
            self.style.NOTICE(f'\n{"="*60}')
        )
        self.stdout.write(
            self.style.NOTICE('STALE USER CLEANUP')
        )
        self.stdout.write(
            self.style.NOTICE(f'{"="*60}')
        )
        self.stdout.write(f'Cutoff date: {cutoff_date}')
        self.stdout.write(f'Days threshold: {days}')
        self.stdout.write(f'Mode: {"DRY RUN" if dry_run else "LIVE DELETE"}')
        self.stdout.write('')

        # Find stale unverified users
        stale_users = User.objects.filter(
            is_email_verified=False,
            created_at__lt=cutoff_date
        ).order_by('created_at')

        total_count = stale_users.count()

        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No stale users found. Database is clean!')
            )
            return

        self.stdout.write(f'Found {total_count} stale unverified user(s)\n')

        if verbosity >= 2:
            self.stdout.write('Users to be deleted:')
            self.stdout.write('-' * 60)
            for user in stale_users[:20]:  # Show first 20
                self.stdout.write(
                    f'  - {user.user_code} | {user.email} | '
                    f'Created: {user.created_at.strftime("%Y-%m-%d %H:%M")}'
                )
            if total_count > 20:
                self.stdout.write(f'  ... and {total_count - 20} more')
            self.stdout.write('')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {total_count} user(s). '
                    f'Run without --dry-run to actually delete.'
                )
            )
            return

        # Confirm deletion
        self.stdout.write(
            self.style.WARNING(
                f'About to permanently delete {total_count} user(s). '
                f'This action cannot be undone!'
            )
        )

        # Delete in batches with transaction
        deleted_count = 0
        failed_count = 0
        
        try:
            with transaction.atomic():
                # Get IDs first to avoid queryset changes during iteration
                user_ids = list(stale_users.values_list('id', flat=True))
                
                for i in range(0, len(user_ids), batch_size):
                    batch_ids = user_ids[i:i + batch_size]
                    batch_users = User.objects.filter(id__in=batch_ids)
                    
                    # Log each deletion for audit
                    for user in batch_users:
                        if verbosity >= 2:
                            self.stdout.write(
                                f'  Deleting: {user.user_code} | {user.email}'
                            )
                    
                    # Perform batch delete
                    count, _ = batch_users.delete()
                    deleted_count += count
                    
                    self.stdout.write(
                        f'  Batch {i//batch_size + 1}: Deleted {count} user(s)'
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during deletion: {str(e)}')
            )
            failed_count = total_count - deleted_count

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE(f'{"="*60}'))
        self.stdout.write(self.style.NOTICE('CLEANUP SUMMARY'))
        self.stdout.write(self.style.NOTICE(f'{"="*60}'))
        self.stdout.write(f'Total stale users found: {total_count}')
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted: {deleted_count}')
        )
        if failed_count > 0:
            self.stdout.write(
                self.style.ERROR(f'Failed to delete: {failed_count}')
            )
        self.stdout.write('')

        # Log the cleanup action
        self.stdout.write(
            self.style.SUCCESS(
                f'Cleanup completed at {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'
            )
        )
