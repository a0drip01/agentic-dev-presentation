"""
Comprehensive test suite for the Kafka-like notification bus system.
Tests models, API endpoints, and the complete notification lifecycle.
"""
import json
import uuid
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import (
    Consumer, ConsumerSubscription, ConsumerNotificationAck,
    ConsumerNotificationPending, Notification, Room
)
from .notification_bus import NotificationBus

User = get_user_model()


class ConsumerModelTests(TestCase):
    """Test the Consumer model functionality"""
    
    def setUp(self):
        self.consumer_data = {
            'name': 'Test Consumer',
            'consumer_type': 'mobile',
            'metadata': {'device_id': 'test_device_123'}
        }
    
    def test_consumer_creation(self):
        """Test creating a consumer"""
        consumer = Consumer.objects.create(**self.consumer_data)
        self.assertEqual(consumer.name, 'Test Consumer')
        self.assertEqual(consumer.consumer_type, 'mobile')
        self.assertEqual(consumer.status, 'active')  # default
        self.assertTrue(consumer.is_active())
        self.assertIsNotNone(consumer.id)  # UUID should be generated
    
    def test_consumer_str_representation(self):
        """Test the string representation of Consumer"""
        consumer = Consumer.objects.create(**self.consumer_data)
        expected = f"{consumer.name} ({consumer.consumer_type})"
        self.assertEqual(str(consumer), expected)
    
    def test_consumer_inactive_status(self):
        """Test inactive consumer status"""
        consumer = Consumer.objects.create(
            **self.consumer_data,
            status='inactive'
        )
        self.assertFalse(consumer.is_active())


class ConsumerSubscriptionModelTests(TestCase):
    """Test the ConsumerSubscription model functionality"""
    
    def setUp(self):
        self.consumer = Consumer.objects.create(
            name='Test Consumer',
            consumer_type='mobile'
        )
    
    def test_subscription_creation(self):
        """Test creating a subscription"""
        subscription = ConsumerSubscription.objects.create(
            consumer=self.consumer,
            tag_type='room',
            tag_value='Room1'
        )
        self.assertEqual(subscription.consumer, self.consumer)
        self.assertEqual(subscription.tag_type, 'room')
        self.assertEqual(subscription.tag_value, 'Room1')
    
    def test_subscription_unique_constraint(self):
        """Test that duplicate subscriptions are prevented"""
        ConsumerSubscription.objects.create(
            consumer=self.consumer,
            tag_type='room',
            tag_value='Room1'
        )
        
        # This should raise an IntegrityError due to unique_together constraint
        with self.assertRaises(Exception):
            ConsumerSubscription.objects.create(
                consumer=self.consumer,
                tag_type='room',
                tag_value='Room1'
            )
    
    def test_subscription_str_representation(self):
        """Test the string representation of ConsumerSubscription"""
        subscription = ConsumerSubscription.objects.create(
            consumer=self.consumer,
            tag_type='room',
            tag_value='Room1'
        )
        expected = f"{self.consumer.name}: room=Room1"
        self.assertEqual(str(subscription), expected)


class ConsumerNotificationAckModelTests(TestCase):
    """Test the ConsumerNotificationAck model functionality"""
    
    def setUp(self):
        self.consumer = Consumer.objects.create(
            name='Test Consumer',
            consumer_type='mobile'
        )
        self.room = Room.objects.create(name='Test Room')
        self.notification = Notification.objects.create(
            room=self.room,
            message='Test notification'
        )
    
    def test_acknowledgment_creation(self):
        """Test creating an acknowledgment"""
        ack = ConsumerNotificationAck.objects.create(
            consumer=self.consumer,
            notification=self.notification
        )
        self.assertEqual(ack.consumer, self.consumer)
        self.assertEqual(ack.notification, self.notification)
        self.assertIsNotNone(ack.acknowledged_at)
    
    def test_acknowledgment_unique_constraint(self):
        """Test that duplicate acknowledgments are prevented"""
        ConsumerNotificationAck.objects.create(
            consumer=self.consumer,
            notification=self.notification
        )
        
        # This should raise an IntegrityError due to unique_together constraint
        with self.assertRaises(Exception):
            ConsumerNotificationAck.objects.create(
                consumer=self.consumer,
                notification=self.notification
            )


class ConsumerAPITests(TestCase):
    """Test the Consumer REST API endpoints"""
    
    def setUp(self):
        self.client = Client()
        
    def test_register_consumer_success(self):
        """Test successful consumer registration"""
        data = {
            'name': 'Test Mobile App',
            'consumer_type': 'mobile',
            'metadata': {'device_id': 'test_device'},
            'subscriptions': [
                {'tag_type': 'room', 'tag_value': 'Room1'},
                {'tag_type': 'provider', 'tag_value': 'doctor123'}
            ]
        }
        
        response = self.client.post(
            '/api/consumers/register/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        
        self.assertIn('consumer_id', response_data)
        self.assertEqual(response_data['name'], 'Test Mobile App')
        self.assertEqual(response_data['consumer_type'], 'mobile')
        self.assertEqual(len(response_data['subscriptions']), 2)
        
        # Verify consumer was created in database
        consumer = Consumer.objects.get(id=response_data['consumer_id'])
        self.assertEqual(consumer.name, 'Test Mobile App')
        self.assertEqual(consumer.subscriptions.count(), 2)
    
    def test_register_consumer_validation_errors(self):
        """Test consumer registration validation"""
        # Missing name
        response = self.client.post(
            '/api/consumers/register/',
            data=json.dumps({'consumer_type': 'mobile'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Consumer name is required', response.json()['error'])
        
        # Invalid consumer type
        response = self.client.post(
            '/api/consumers/register/',
            data=json.dumps({
                'name': 'Test',
                'consumer_type': 'invalid_type'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid consumer_type', response.json()['error'])
    
    def test_unregister_consumer(self):
        """Test consumer unregistration"""
        consumer = Consumer.objects.create(
            name='Test Consumer',
            consumer_type='mobile'
        )
        
        response = self.client.delete(f'/api/consumers/{consumer.id}/')
        self.assertEqual(response.status_code, 200)
        
        # Verify consumer was deleted
        self.assertFalse(Consumer.objects.filter(id=consumer.id).exists())
    
    def test_manage_subscriptions_get(self):
        """Test getting consumer subscriptions"""
        consumer = Consumer.objects.create(
            name='Test Consumer',
            consumer_type='mobile'
        )
        ConsumerSubscription.objects.create(
            consumer=consumer,
            tag_type='room',
            tag_value='Room1'
        )
        
        response = self.client.get(f'/api/consumers/{consumer.id}/subscriptions/')
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertEqual(len(response_data['subscriptions']), 1)
        self.assertEqual(response_data['subscriptions'][0]['tag_type'], 'room')
    
    def test_manage_subscriptions_put(self):
        """Test updating consumer subscriptions"""
        consumer = Consumer.objects.create(
            name='Test Consumer',
            consumer_type='mobile'
        )
        
        # Add initial subscription
        ConsumerSubscription.objects.create(
            consumer=consumer,
            tag_type='room',
            tag_value='Room1'
        )
        
        # Update subscriptions
        data = {
            'subscriptions': [
                {'tag_type': 'room', 'tag_value': 'Room2'},
                {'tag_type': 'provider', 'tag_value': 'doctor123'}
            ]
        }
        
        response = self.client.put(
            f'/api/consumers/{consumer.id}/subscriptions/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify subscriptions were updated
        self.assertEqual(consumer.subscriptions.count(), 2)
        self.assertTrue(
            consumer.subscriptions.filter(tag_type='room', tag_value='Room2').exists()
        )
        self.assertFalse(
            consumer.subscriptions.filter(tag_type='room', tag_value='Room1').exists()
        )


class NotificationPollingTests(TestCase):
    """Test notification polling functionality"""
    
    def setUp(self):
        self.consumer = Consumer.objects.create(
            name='Test Consumer',
            consumer_type='mobile'
        )
        ConsumerSubscription.objects.create(
            consumer=self.consumer,
            tag_type='room',
            tag_value='Room1'
        )
        
        self.room = Room.objects.create(name='Room1')
        self.notification = Notification.objects.create(
            room=self.room,
            message='Test notification'
        )
        
        # Create pending notification
        ConsumerNotificationPending.objects.create(
            consumer=self.consumer,
            notification=self.notification,
            matched_tags={'room': 'Room1'}
        )
    
    def test_poll_notifications_success(self):
        """Test successful notification polling"""
        response = self.client.get(f'/api/consumers/{self.consumer.id}/notifications/')
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertEqual(len(response_data['notifications']), 1)
        self.assertEqual(response_data['notifications'][0]['message'], 'Test notification')
        self.assertFalse(response_data['has_more'])
    
    def test_poll_notifications_with_limit(self):
        """Test notification polling with limit parameter"""
        # Create multiple notifications
        for i in range(5):
            notification = Notification.objects.create(
                room=self.room,
                message=f'Test notification {i}'
            )
            ConsumerNotificationPending.objects.create(
                consumer=self.consumer,
                notification=notification,
                matched_tags={'room': 'Room1'}
            )
        
        response = self.client.get(
            f'/api/consumers/{self.consumer.id}/notifications/?limit=3'
        )
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertEqual(len(response_data['notifications']), 3)
        self.assertTrue(response_data['has_more'])
    
    def test_poll_notifications_inactive_consumer(self):
        """Test polling with inactive consumer"""
        self.consumer.status = 'inactive'
        self.consumer.save()
        
        response = self.client.get(f'/api/consumers/{self.consumer.id}/notifications/')
        self.assertEqual(response.status_code, 403)
        self.assertIn('Consumer is not active', response.json()['error'])


class NotificationAcknowledgmentTests(TestCase):
    """Test notification acknowledgment functionality"""
    
    def setUp(self):
        self.consumer = Consumer.objects.create(
            name='Test Consumer',
            consumer_type='mobile'
        )
        self.room = Room.objects.create(name='Room1')
        self.notification = Notification.objects.create(
            room=self.room,
            message='Test notification'
        )
        
        # Create pending notification
        self.pending = ConsumerNotificationPending.objects.create(
            consumer=self.consumer,
            notification=self.notification,
            matched_tags={'room': 'Room1'}
        )
    
    def test_acknowledge_notifications_success(self):
        """Test successful notification acknowledgment"""
        data = {
            'notification_ids': [str(self.notification.id)]
        }
        
        response = self.client.post(
            f'/api/consumers/{self.consumer.id}/notifications/ack/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertEqual(len(response_data['acknowledged']), 1)
        self.assertEqual(len(response_data['errors']), 0)
        self.assertEqual(response_data['success_count'], 1)
        
        # Verify acknowledgment was created
        self.assertTrue(
            ConsumerNotificationAck.objects.filter(
                consumer=self.consumer,
                notification=self.notification
            ).exists()
        )
        
        # Verify pending notification was removed
        self.assertFalse(
            ConsumerNotificationPending.objects.filter(
                consumer=self.consumer,
                notification=self.notification
            ).exists()
        )
    
    def test_acknowledge_notifications_idempotent(self):
        """Test that acknowledgment is idempotent"""
        # First acknowledgment
        ConsumerNotificationAck.objects.create(
            consumer=self.consumer,
            notification=self.notification
        )
        # Remove pending notification (simulating first ack)
        self.pending.delete()
        
        data = {
            'notification_ids': [str(self.notification.id)]
        }
        
        response = self.client.post(
            f'/api/consumers/{self.consumer.id}/notifications/ack/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)  # No pending notifications
        
        response_data = response.json()
        self.assertEqual(len(response_data['acknowledged']), 0)
        self.assertEqual(len(response_data['errors']), 1)
        self.assertIn('not subscribed', response_data['errors'][0]['error'])
    
    def test_acknowledge_notifications_validation(self):
        """Test acknowledgment validation"""
        # Invalid UUID
        data = {
            'notification_ids': ['invalid-uuid']
        }
        
        response = self.client.post(
            f'/api/consumers/{self.consumer.id}/notifications/ack/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid UUID format', response.json()['error'])
        
        # Empty list
        data = {
            'notification_ids': []
        }
        
        response = self.client.post(
            f'/api/consumers/{self.consumer.id}/notifications/ack/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('cannot be empty', response.json()['error'])


class NotificationBusIntegrationTests(TestCase):
    """Test the complete notification bus workflow"""
    
    def setUp(self):
        # Create a room and users
        self.room = Room.objects.create(name='Test Room')
        
        # Create consumers with different subscription types
        self.mobile_consumer = Consumer.objects.create(
            name='Mobile App',
            consumer_type='mobile'
        )
        ConsumerSubscription.objects.create(
            consumer=self.mobile_consumer,
            tag_type='room',
            tag_value='Test Room'
        )
        
        self.provider_consumer = Consumer.objects.create(
            name='Provider App',
            consumer_type='service'
        )
        ConsumerSubscription.objects.create(
            consumer=self.provider_consumer,
            tag_type='all',
            tag_value='all'
        )
    
    def test_complete_notification_lifecycle(self):
        """Test the complete notification lifecycle from publish to acknowledgment"""
        # Step 1: Publish a notification
        notification = NotificationBus.publish(self.room, 'Test room notification')
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.room, self.room)
        self.assertEqual(notification.message, 'Test room notification')
        
        # Step 2: Verify pending notifications were created for matching consumers
        mobile_pending = ConsumerNotificationPending.objects.filter(
            consumer=self.mobile_consumer,
            notification=notification
        )
        self.assertTrue(mobile_pending.exists())
        
        provider_pending = ConsumerNotificationPending.objects.filter(
            consumer=self.provider_consumer,
            notification=notification
        )
        self.assertTrue(provider_pending.exists())
        
        # Step 3: Mobile consumer polls for notifications
        response = self.client.get(f'/api/consumers/{self.mobile_consumer.id}/notifications/')
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertEqual(len(response_data['notifications']), 1)
        self.assertEqual(response_data['notifications'][0]['id'], str(notification.id))
        
        # Step 4: Mobile consumer acknowledges the notification
        ack_data = {
            'notification_ids': [str(notification.id)]
        }
        
        response = self.client.post(
            f'/api/consumers/{self.mobile_consumer.id}/notifications/ack/',
            data=json.dumps(ack_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Step 5: Verify acknowledgment was recorded and pending removed for mobile
        self.assertTrue(
            ConsumerNotificationAck.objects.filter(
                consumer=self.mobile_consumer,
                notification=notification
            ).exists()
        )
        self.assertFalse(
            ConsumerNotificationPending.objects.filter(
                consumer=self.mobile_consumer,
                notification=notification
            ).exists()
        )
        
        # Step 6: Verify provider consumer still has pending notification
        self.assertTrue(
            ConsumerNotificationPending.objects.filter(
                consumer=self.provider_consumer,
                notification=notification
            ).exists()
        )
        
        # Step 7: Provider consumer also acknowledges
        response = self.client.post(
            f'/api/consumers/{self.provider_consumer.id}/notifications/ack/',
            data=json.dumps(ack_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Step 8: Verify all pending notifications are cleared
        self.assertEqual(
            ConsumerNotificationPending.objects.filter(
                notification=notification
            ).count(),
            0
        )
    
    def test_consumer_status_endpoint(self):
        """Test the consumer status endpoint"""
        response = self.client.get(f'/api/consumers/{self.mobile_consumer.id}/status/')
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertEqual(response_data['consumer_id'], str(self.mobile_consumer.id))
        self.assertEqual(response_data['name'], 'Mobile App')
        self.assertEqual(response_data['consumer_type'], 'mobile')
        self.assertEqual(response_data['status'], 'active')
        
        stats = response_data['stats']
        self.assertEqual(stats['subscription_count'], 1)
        self.assertIn('pending_notification_count', stats)
        self.assertIn('total_acknowledgments', stats)


class ManagementCommandTests(TestCase):
    """Test management commands"""
    
    def setUp(self):
        self.consumer = Consumer.objects.create(
            name='Test Consumer',
            consumer_type='mobile'
        )
        self.room = Room.objects.create(name='Test Room')
        self.notification = Notification.objects.create(
            room=self.room,
            message='Test notification'
        )
    
    def test_cleanup_old_acknowledgments_dry_run(self):
        """Test cleanup acknowledgments command in dry run mode"""
        from django.core.management import call_command
        from io import StringIO
        
        # Create an old acknowledgment
        old_ack = ConsumerNotificationAck.objects.create(
            consumer=self.consumer,
            notification=self.notification
        )
        # Manually set an old timestamp
        old_time = timezone.now() - timedelta(days=35)
        ConsumerNotificationAck.objects.filter(id=old_ack.id).update(acknowledged_at=old_time)
        
        out = StringIO()
        call_command('cleanup_old_acknowledgments', '--dry-run', '--days=30', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Would delete 1 acknowledgment records', output)
        
        # Verify nothing was actually deleted
        self.assertTrue(ConsumerNotificationAck.objects.filter(id=old_ack.id).exists())
    
    def test_db_maintenance_stats(self):
        """Test database maintenance statistics command"""
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('db_maintenance', '--stats', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Notification Bus Database Statistics', output)
        self.assertIn('Consumers:', output)
        self.assertIn('Notifications:', output)
