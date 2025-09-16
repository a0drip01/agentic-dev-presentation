"""
Management command to clean up old acknowledgment records.
Removes acknowledgment records older than a specified number of days.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from core.models import ConsumerNotificationAck
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up old consumer notification acknowledgment records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Remove acknowledgment records older than this many days (default: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Process records in batches of this size (default: 1000)'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        if days <= 0:
            raise CommandError('Days must be a positive integer')
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f"Looking for acknowledgment records older than {days} days (before {cutoff_date})...")
        
        # Get the queryset
        old_acks = ConsumerNotificationAck.objects.filter(
            acknowledged_at__lt=cutoff_date
        )
        
        total_count = old_acks.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No old acknowledgment records found to clean up.')
            )
            return
        
        self.stdout.write(f"Found {total_count} acknowledgment records to clean up.")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would delete {total_count} acknowledgment records')
            )
            # Show some examples
            sample_acks = old_acks[:5]
            for ack in sample_acks:
                self.stdout.write(f"  - Consumer: {ack.consumer.name}, Notification: {ack.notification.id}, Acked: {ack.acknowledged_at}")
            if total_count > 5:
                self.stdout.write(f"  ... and {total_count - 5} more")
            return
        
        # Confirm deletion for large numbers
        if total_count > 10000:
            confirm = input(f"This will delete {total_count} records. Are you sure? (yes/no): ")
            if confirm.lower() != 'yes':
                self.stdout.write('Operation cancelled.')
                return
        
        # Delete in batches to avoid memory issues
        deleted_count = 0
        
        with transaction.atomic():
            while True:
                # Get a batch of IDs to delete
                batch_ids = list(
                    ConsumerNotificationAck.objects.filter(
                        acknowledged_at__lt=cutoff_date
                    ).values_list('id', flat=True)[:batch_size]
                )
                
                if not batch_ids:
                    break
                
                # Delete this batch
                batch_deleted = ConsumerNotificationAck.objects.filter(
                    id__in=batch_ids
                ).delete()[0]
                
                deleted_count += batch_deleted
                
                self.stdout.write(f"Deleted batch of {batch_deleted} records... (total: {deleted_count})")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleaned up {deleted_count} old acknowledgment records.')
        )
        
        # Log the cleanup
        logger.info(f"Cleaned up {deleted_count} acknowledgment records older than {days} days")