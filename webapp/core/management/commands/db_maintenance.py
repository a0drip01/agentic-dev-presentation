"""
Management command for database maintenance and optimization.
Provides statistics and performs maintenance tasks for the notification bus system.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from core.models import (
    Consumer, ConsumerSubscription, ConsumerNotificationAck, 
    ConsumerNotificationPending, Notification
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Database maintenance and optimization for the notification bus system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Display database statistics'
        )
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='Vacuum the database (SQLite only)'
        )
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze tables to update query planner statistics'
        )
        parser.add_argument(
            '--check-performance',
            action='store_true',
            help='Check for potential performance issues'
        )

    def handle(self, *args, **options):
        if options['stats']:
            self.show_statistics()
        
        if options['check_performance']:
            self.check_performance()
        
        if options['vacuum']:
            self.vacuum_database()
        
        if options['analyze']:
            self.analyze_database()
        
        if not any([options['stats'], options['vacuum'], options['analyze'], options['check_performance']]):
            self.stdout.write("No operation specified. Use --help to see available options.")

    def show_statistics(self):
        """Display comprehensive database statistics"""
        self.stdout.write(self.style.SUCCESS("\n=== Notification Bus Database Statistics ==="))
        
        # Consumer statistics
        total_consumers = Consumer.objects.count()
        active_consumers = Consumer.objects.filter(status='active').count()
        inactive_consumers = Consumer.objects.filter(status='inactive').count()
        suspended_consumers = Consumer.objects.filter(status='suspended').count()
        
        self.stdout.write(f"\nConsumers:")
        self.stdout.write(f"  Total: {total_consumers}")
        self.stdout.write(f"  Active: {active_consumers}")
        self.stdout.write(f"  Inactive: {inactive_consumers}")
        self.stdout.write(f"  Suspended: {suspended_consumers}")
        
        # Consumer type breakdown
        consumer_types = set(Consumer.objects.values_list('consumer_type', flat=True))
        for consumer_type in consumer_types:
            count = Consumer.objects.filter(consumer_type=consumer_type).count()
            self.stdout.write(f"  {consumer_type.title()}: {count}")
        
        # Subscription statistics
        total_subscriptions = ConsumerSubscription.objects.count()
        self.stdout.write(f"\nSubscriptions:")
        self.stdout.write(f"  Total: {total_subscriptions}")
        
        # Subscription type breakdown
        sub_types = set(ConsumerSubscription.objects.values_list('tag_type', flat=True))
        for sub_type in sub_types:
            count = ConsumerSubscription.objects.filter(tag_type=sub_type).count()
            self.stdout.write(f"  {sub_type.title()}: {count}")
        
        # Notification statistics
        total_notifications = Notification.objects.count()
        recent_notifications = Notification.objects.filter(
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        self.stdout.write(f"\nNotifications:")
        self.stdout.write(f"  Total: {total_notifications}")
        self.stdout.write(f"  Last 7 days: {recent_notifications}")
        
        # Acknowledgment statistics
        total_acks = ConsumerNotificationAck.objects.count()
        recent_acks = ConsumerNotificationAck.objects.filter(
            acknowledged_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        self.stdout.write(f"\nAcknowledgments:")
        self.stdout.write(f"  Total: {total_acks}")
        self.stdout.write(f"  Last 7 days: {recent_acks}")
        
        # Pending notifications
        total_pending = ConsumerNotificationPending.objects.count()
        
        self.stdout.write(f"\nPending Notifications:")
        self.stdout.write(f"  Total: {total_pending}")
        
        # Show pending by consumer
        if total_pending > 0:
            pending_by_consumer = ConsumerNotificationPending.objects.select_related('consumer')\
                .values('consumer__name')\
                .annotate(pending_count=Count('id'))\
                .order_by('-pending_count')[:10]
            
            for item in pending_by_consumer:
                consumer_name = item['consumer__name']
                count = item['pending_count']
                self.stdout.write(f"  {consumer_name}: {count}")
        
        # Database size information
        with connection.cursor() as cursor:
            # This works for SQLite
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                self.stdout.write(f"\nDatabase Tables:")
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    self.stdout.write(f"  {table_name}: {count} rows")
            except Exception as e:
                self.stdout.write(f"\nCould not retrieve table information: {e}")

    def check_performance(self):
        """Check for potential performance issues"""
        self.stdout.write(self.style.SUCCESS("\n=== Performance Analysis ==="))
        
        # Check for consumers with too many pending notifications
        high_pending_consumers = ConsumerNotificationPending.objects.values('consumer__name')\
            .annotate(pending_count=Count('id'))\
            .filter(pending_count__gt=1000)\
            .order_by('-pending_count')
        
        if high_pending_consumers:
            self.stdout.write(self.style.WARNING("\nConsumers with high pending notification counts:"))
            for consumer in high_pending_consumers:
                self.stdout.write(f"  {consumer['consumer__name']}: {consumer['pending_count']} pending")
        
        # Check for old pending notifications
        old_pending = ConsumerNotificationPending.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=7)
        ).count()
        
        if old_pending > 0:
            self.stdout.write(self.style.WARNING(f"\nFound {old_pending} pending notifications older than 7 days"))
        
        # Check for consumers not seen recently
        inactive_consumers = Consumer.objects.filter(
            status='active',
            last_seen_at__lt=timezone.now() - timedelta(days=3)
        ).count()
        
        if inactive_consumers > 0:
            self.stdout.write(self.style.WARNING(f"\nFound {inactive_consumers} active consumers not seen in 3+ days"))
        
        # Check for duplicate subscriptions (shouldn't happen due to unique constraint)
        duplicate_subs = ConsumerSubscription.objects.values('consumer', 'tag_type', 'tag_value')\
            .annotate(count=Count('id')).filter(count__gt=1)
        
        if duplicate_subs:
            self.stdout.write(self.style.ERROR(f"\nFound {duplicate_subs.count()} duplicate subscriptions (this shouldn't happen!)"))
        
        self.stdout.write(self.style.SUCCESS("\nPerformance check completed."))

    def vacuum_database(self):
        """Vacuum the database to reclaim space (SQLite only)"""
        self.stdout.write("Vacuuming database...")
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("VACUUM;")
            self.stdout.write(self.style.SUCCESS("Database vacuum completed."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Vacuum failed: {e}"))

    def analyze_database(self):
        """Analyze database tables to update query planner statistics"""
        self.stdout.write("Analyzing database tables...")
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("ANALYZE;")
            self.stdout.write(self.style.SUCCESS("Database analysis completed."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Analysis failed: {e}"))