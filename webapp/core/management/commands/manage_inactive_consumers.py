"""
Management command to handle inactive consumers.
Marks consumers as inactive based on their last_seen_at timestamp and optionally cleans up their data.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from core.models import Consumer, ConsumerNotificationPending, ConsumerNotificationAck
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage inactive consumers and optionally clean up their data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--inactive-days',
            type=int,
            default=7,
            help='Mark consumers as inactive if not seen for this many days (default: 7)'
        )
        parser.add_argument(
            '--cleanup-days',
            type=int,
            default=30,
            help='Remove pending notifications for consumers inactive for this many days (default: 30)'
        )
        parser.add_argument(
            '--delete-days',
            type=int,
            default=90,
            help='Delete consumers completely if inactive for this many days (default: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually making changes'
        )
        parser.add_argument(
            '--mark-inactive-only',
            action='store_true',
            help='Only mark consumers as inactive, do not clean up or delete'
        )

    def handle(self, *args, **options):
        inactive_days = options['inactive_days']
        cleanup_days = options['cleanup_days']
        delete_days = options['delete_days']
        dry_run = options['dry_run']
        mark_inactive_only = options['mark_inactive_only']
        
        if inactive_days <= 0 or cleanup_days <= 0 or delete_days <= 0:
            raise CommandError('All day values must be positive integers')
        
        if cleanup_days <= inactive_days:
            raise CommandError('cleanup-days must be greater than inactive-days')
        
        if delete_days <= cleanup_days:
            raise CommandError('delete-days must be greater than cleanup-days')
        
        now = timezone.now()
        inactive_cutoff = now - timedelta(days=inactive_days)
        cleanup_cutoff = now - timedelta(days=cleanup_days)
        delete_cutoff = now - timedelta(days=delete_days)
        
        self.stdout.write(f"Processing consumers with the following thresholds:")
        self.stdout.write(f"  - Mark inactive: not seen since {inactive_cutoff} ({inactive_days} days)")
        self.stdout.write(f"  - Clean up pending notifications: not seen since {cleanup_cutoff} ({cleanup_days} days)")
        self.stdout.write(f"  - Delete completely: not seen since {delete_cutoff} ({delete_days} days)")
        
        # Phase 1: Mark consumers as inactive
        consumers_to_mark_inactive = Consumer.objects.filter(
            status='active',
            last_seen_at__lt=inactive_cutoff
        )
        
        inactive_count = consumers_to_mark_inactive.count()
        
        if inactive_count > 0:
            self.stdout.write(f"\nFound {inactive_count} active consumers to mark as inactive:")
            for consumer in consumers_to_mark_inactive:
                self.stdout.write(f"  - {consumer.name} (last seen: {consumer.last_seen_at})")
            
            if not dry_run:
                with transaction.atomic():
                    updated = consumers_to_mark_inactive.update(status='inactive')
                self.stdout.write(
                    self.style.SUCCESS(f'Marked {updated} consumers as inactive.')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'DRY RUN: Would mark {inactive_count} consumers as inactive')
                )
        else:
            self.stdout.write("\nNo active consumers found that need to be marked inactive.")
        
        if mark_inactive_only:
            return
        
        # Phase 2: Clean up pending notifications for very inactive consumers
        consumers_to_cleanup = Consumer.objects.filter(
            last_seen_at__lt=cleanup_cutoff
        )
        
        cleanup_consumer_count = consumers_to_cleanup.count()
        
        if cleanup_consumer_count > 0:
            # Count pending notifications to be cleaned up
            pending_to_cleanup = ConsumerNotificationPending.objects.filter(
                consumer__in=consumers_to_cleanup
            )
            pending_count = pending_to_cleanup.count()
            
            if pending_count > 0:
                self.stdout.write(f"\nFound {pending_count} pending notifications for {cleanup_consumer_count} very inactive consumers:")
                
                # Show some examples
                consumer_pending_counts = {}
                for pending in pending_to_cleanup[:10]:
                    consumer_name = pending.consumer.name
                    consumer_pending_counts[consumer_name] = consumer_pending_counts.get(consumer_name, 0) + 1
                
                for consumer_name, count in consumer_pending_counts.items():
                    self.stdout.write(f"  - {consumer_name}: {count} pending notifications")
                
                if pending_count > 10:
                    self.stdout.write(f"  ... and more")
                
                if not dry_run:
                    with transaction.atomic():
                        deleted_count = pending_to_cleanup.delete()[0]
                    self.stdout.write(
                        self.style.SUCCESS(f'Cleaned up {deleted_count} pending notifications.')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'DRY RUN: Would clean up {pending_count} pending notifications')
                    )
            else:
                self.stdout.write(f"\nNo pending notifications found to clean up for very inactive consumers.")
        
        # Phase 3: Delete consumers that have been inactive for a very long time
        consumers_to_delete = Consumer.objects.filter(
            last_seen_at__lt=delete_cutoff
        )
        
        delete_count = consumers_to_delete.count()
        
        if delete_count > 0:
            self.stdout.write(f"\nFound {delete_count} consumers to delete completely (inactive > {delete_days} days):")
            
            for consumer in consumers_to_delete:
                ack_count = consumer.acknowledgments.count()
                pending_count = consumer.pending_notifications.count()
                sub_count = consumer.subscriptions.count()
                self.stdout.write(
                    f"  - {consumer.name} (last seen: {consumer.last_seen_at}) "
                    f"[{ack_count} acks, {pending_count} pending, {sub_count} subscriptions]"
                )
            
            if not dry_run:
                confirm = input(f"This will permanently delete {delete_count} consumers and all their data. Are you sure? (yes/no): ")
                if confirm.lower() == 'yes':
                    with transaction.atomic():
                        deleted_counts = consumers_to_delete.delete()
                        total_deleted = deleted_counts[0]
                        
                    self.stdout.write(
                        self.style.SUCCESS(f'Deleted {total_deleted} inactive consumers and all their related data.')
                    )
                    
                    # Show breakdown of what was deleted
                    if len(deleted_counts[1]) > 1:
                        self.stdout.write("Deleted records breakdown:")
                        for model_name, count in deleted_counts[1].items():
                            self.stdout.write(f"  - {model_name}: {count}")
                else:
                    self.stdout.write('Consumer deletion cancelled.')
            else:
                self.stdout.write(
                    self.style.WARNING(f'DRY RUN: Would delete {delete_count} consumers completely')
                )
        else:
            self.stdout.write(f"\nNo consumers found to delete completely.")
        
        # Log the operation
        logger.info(
            f"Inactive consumer management completed. "
            f"Marked {inactive_count} as inactive, "
            f"cleaned up pending for {cleanup_consumer_count} consumers, "
            f"identified {delete_count} for deletion"
        )