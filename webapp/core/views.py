from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from .models import Consumer, ConsumerSubscription, Notification, ConsumerNotificationAck, ConsumerNotificationPending
import json
import uuid

# Create your views here.

@csrf_exempt
@require_http_methods(["POST"])
def register_consumer(request):
    """
    POST /api/consumers/register/
    Register a new consumer with optional subscriptions.
    
    Expected JSON payload:
    {
        "name": "My Mobile App",
        "consumer_type": "mobile",  # mobile, script, service, webhook
        "metadata": {"device_id": "...", "app_version": "1.0"},  # optional
        "subscriptions": [  # optional
            {"tag_type": "room", "tag_value": "Room1"},
            {"tag_type": "provider", "tag_value": "12345"}
        ]
    }
    """
    try:
        # Parse JSON payload
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON payload'
            }, status=400)
        
        # Validate required fields
        name = data.get('name', '').strip()
        if not name:
            return JsonResponse({
                'error': 'Consumer name is required'
            }, status=400)
        
        consumer_type = data.get('consumer_type', 'mobile')
        valid_types = [choice[0] for choice in Consumer.CONSUMER_TYPES]
        if consumer_type not in valid_types:
            return JsonResponse({
                'error': f'Invalid consumer_type. Must be one of: {valid_types}'
            }, status=400)
        
        metadata = data.get('metadata', {})
        if not isinstance(metadata, dict):
            return JsonResponse({
                'error': 'metadata must be a JSON object'
            }, status=400)
        
        subscriptions_data = data.get('subscriptions', [])
        if not isinstance(subscriptions_data, list):
            return JsonResponse({
                'error': 'subscriptions must be a list'
            }, status=400)
        
        # Validate subscriptions
        valid_tag_types = [choice[0] for choice in ConsumerSubscription.TAG_TYPES]
        for sub in subscriptions_data:
            if not isinstance(sub, dict):
                return JsonResponse({
                    'error': 'Each subscription must be a JSON object'
                }, status=400)
            
            tag_type = sub.get('tag_type', '').strip()
            tag_value = sub.get('tag_value', '').strip()
            
            if not tag_type or not tag_value:
                return JsonResponse({
                    'error': 'Each subscription must have tag_type and tag_value'
                }, status=400)
            
            if tag_type not in valid_tag_types:
                return JsonResponse({
                    'error': f'Invalid tag_type "{tag_type}". Must be one of: {valid_tag_types}'
                }, status=400)
        
        # Create consumer and subscriptions in a transaction
        with transaction.atomic():
            consumer = Consumer.objects.create(
                name=name,
                consumer_type=consumer_type,
                metadata=metadata
            )
            
            # Create subscriptions
            created_subscriptions = []
            for sub in subscriptions_data:
                try:
                    subscription = ConsumerSubscription.objects.create(
                        consumer=consumer,
                        tag_type=sub['tag_type'],
                        tag_value=sub['tag_value']
                    )
                    created_subscriptions.append({
                        'tag_type': subscription.tag_type,
                        'tag_value': subscription.tag_value,
                        'created_at': subscription.created_at.isoformat()
                    })
                except IntegrityError:
                    # Duplicate subscription - skip but don't error
                    continue
        
        # Return success response
        return JsonResponse({
            'consumer_id': str(consumer.id),
            'name': consumer.name,
            'consumer_type': consumer.consumer_type,
            'status': consumer.status,
            'registered_at': consumer.registered_at.isoformat(),
            'metadata': consumer.metadata,
            'subscriptions': created_subscriptions
        }, status=201)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def unregister_consumer(request, consumer_id):
    """
    DELETE /api/consumers/{id}/
    Unregister a consumer and clean up its data.
    This will delete the consumer, its subscriptions, and all acknowledgment records.
    """
    try:
        consumer = get_object_or_404(Consumer, id=consumer_id)
        
        # Collect stats before deletion
        subscription_count = consumer.subscriptions.count()
        ack_count = consumer.acknowledgments.count()
        pending_count = consumer.pending_notifications.count()
        consumer_name = consumer.name
        
        # Delete the consumer (this will cascade to related objects)
        with transaction.atomic():
            consumer.delete()
        
        return JsonResponse({
            'message': f'Consumer "{consumer_name}" successfully unregistered',
            'deleted_records': {
                'consumer': 1,
                'subscriptions': subscription_count,
                'acknowledgments': ack_count,
                'pending_notifications': pending_count
            }
        })
        
    except Consumer.DoesNotExist:
        return JsonResponse({
            'error': 'Consumer not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def manage_subscriptions(request, consumer_id):
    """
    GET /api/consumers/{id}/subscriptions/ - List consumer subscriptions
    PUT /api/consumers/{id}/subscriptions/ - Update consumer subscriptions  
    DELETE /api/consumers/{id}/subscriptions/ - Clear all subscriptions
    """
    try:
        # Get the consumer
        consumer = get_object_or_404(Consumer, id=consumer_id)
        
        if not consumer.is_active():
            return JsonResponse({
                'error': 'Consumer is not active'
            }, status=403)
        
        # Update last_seen_at
        consumer.save()  # This triggers auto_now on last_seen_at
        
        if request.method == 'GET':
            # List current subscriptions
            subscriptions = consumer.subscriptions.all()
            subscription_list = []
            for sub in subscriptions:
                subscription_list.append({
                    'tag_type': sub.tag_type,
                    'tag_value': sub.tag_value,
                    'created_at': sub.created_at.isoformat()
                })
            
            return JsonResponse({
                'consumer_id': str(consumer.id),
                'consumer_name': consumer.name,
                'subscriptions': subscription_list
            })
        
        elif request.method == 'PUT':
            # Update subscriptions (replace all)
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'error': 'Invalid JSON payload'
                }, status=400)
            
            subscriptions_data = data.get('subscriptions', [])
            if not isinstance(subscriptions_data, list):
                return JsonResponse({
                    'error': 'subscriptions must be a list'
                }, status=400)
            
            # Validate subscriptions
            valid_tag_types = [choice[0] for choice in ConsumerSubscription.TAG_TYPES]
            for sub in subscriptions_data:
                if not isinstance(sub, dict):
                    return JsonResponse({
                        'error': 'Each subscription must be a JSON object'
                    }, status=400)
                
                tag_type = sub.get('tag_type', '').strip()
                tag_value = sub.get('tag_value', '').strip()
                
                if not tag_type or not tag_value:
                    return JsonResponse({
                        'error': 'Each subscription must have tag_type and tag_value'
                    }, status=400)
                
                if tag_type not in valid_tag_types:
                    return JsonResponse({
                        'error': f'Invalid tag_type "{tag_type}". Must be one of: {valid_tag_types}'
                    }, status=400)
            
            # Replace all subscriptions in a transaction
            with transaction.atomic():
                # Clear existing subscriptions
                consumer.subscriptions.all().delete()
                
                # Create new subscriptions
                created_subscriptions = []
                for sub in subscriptions_data:
                    try:
                        subscription = ConsumerSubscription.objects.create(
                            consumer=consumer,
                            tag_type=sub['tag_type'],
                            tag_value=sub['tag_value']
                        )
                        created_subscriptions.append({
                            'tag_type': subscription.tag_type,
                            'tag_value': subscription.tag_value,
                            'created_at': subscription.created_at.isoformat()
                        })
                    except IntegrityError:
                        # Duplicate subscription - skip but don't error
                        continue
            
            return JsonResponse({
                'consumer_id': str(consumer.id),
                'message': 'Subscriptions updated successfully',
                'subscriptions': created_subscriptions
            })
        
        elif request.method == 'DELETE':
            # Clear all subscriptions
            deleted_count = consumer.subscriptions.count()
            consumer.subscriptions.all().delete()
            
            return JsonResponse({
                'consumer_id': str(consumer.id),
                'message': f'Cleared {deleted_count} subscriptions'
            })
    
    except Consumer.DoesNotExist:
        return JsonResponse({
            'error': 'Consumer not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def poll_notifications(request, consumer_id):
    """
    GET /api/consumers/{id}/notifications/
    Poll for unacknowledged notifications for this consumer.
    
    Query parameters:
    - since: ISO timestamp (optional) - only return notifications after this time
    - limit: integer (optional) - max number of notifications to return (default 50)
    """
    try:
        # Get and validate the consumer
        consumer = get_object_or_404(Consumer, id=consumer_id)
        
        if not consumer.is_active():
            return JsonResponse({
                'error': 'Consumer is not active'
            }, status=403)
        
        # Update consumer's last_seen_at
        consumer.save()  # This triggers auto_now on last_seen_at
        
        # Parse query parameters
        since_param = request.GET.get('since')
        limit_param = request.GET.get('limit', '50')
        
        # Validate and parse limit
        try:
            limit = int(limit_param)
            if limit <= 0:
                limit = 50
            elif limit > 100:  # Cap at 100 for performance
                limit = 100
        except ValueError:
            return JsonResponse({
                'error': 'Invalid limit parameter. Must be a positive integer.'
            }, status=400)
        
        # Parse since timestamp if provided
        since_dt = None
        if since_param:
            from django.utils.dateparse import parse_datetime
            since_dt = parse_datetime(since_param)
            if since_dt is None:
                return JsonResponse({
                    'error': 'Invalid since parameter. Must be ISO 8601 timestamp.'
                }, status=400)
        
        # Get pending notifications for this consumer
        # These are notifications that match the consumer's subscriptions
        # and haven't been acknowledged yet
        pending_qs = consumer.pending_notifications.select_related('notification', 'notification__room')
        
        # Apply time filtering if since parameter provided
        if since_dt:
            pending_qs = pending_qs.filter(notification__timestamp__gt=since_dt)
        
        # Order by notification timestamp (newest first) and apply limit + 1
        # We get one extra to check if there are more results
        pending_qs = pending_qs.order_by('-notification__timestamp')[:limit + 1]
        
        # Convert to list to evaluate the queryset
        pending_list = list(pending_qs)
        
        # Check if there are more results
        has_more = len(pending_list) > limit
        if has_more:
            pending_list = pending_list[:limit]  # Remove the extra one
        
        # Build the response
        notifications = []
        next_since = None
        
        for pending in pending_list:
            notification = pending.notification
            
            # Extract tags for the notification (same logic as notification bus)
            from .notification_bus import NotificationBus
            tags = NotificationBus.extract_tags_from_notification(notification)
            
            notifications.append({
                'id': str(notification.id),
                'room': notification.room.name,
                'message': notification.message,
                'timestamp': notification.timestamp.isoformat(),
                'tags': tags
            })
            
            # Track the timestamp for next_since
            next_since = notification.timestamp.isoformat()
        
        return JsonResponse({
            'notifications': notifications,
            'has_more': has_more,
            'next_since': next_since,
            'consumer_id': str(consumer.id),
            'count': len(notifications)
        })
        
    except Http404:
        return JsonResponse({
            'error': 'Consumer not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def acknowledge_notifications(request, consumer_id):
    """
    POST /api/consumers/{id}/notifications/ack/
    Acknowledge one or more notifications as processed.
    
    Expected JSON payload:
    {
        "notification_ids": ["uuid-1", "uuid-2", "uuid-3"]
    }
    
    Returns success/error status for each notification ID.
    This endpoint is idempotent - acknowledging the same notification multiple times is safe.
    """
    try:
        # Get and validate the consumer
        consumer = get_object_or_404(Consumer, id=consumer_id)
        
        if not consumer.is_active():
            return JsonResponse({
                'error': 'Consumer is not active'
            }, status=403)
        
        # Update consumer's last_seen_at
        consumer.save()  # This triggers auto_now on last_seen_at
        
        # Parse JSON payload
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON payload'
            }, status=400)
        
        # Validate notification_ids field
        notification_ids = data.get('notification_ids', [])
        if not isinstance(notification_ids, list):
            return JsonResponse({
                'error': 'notification_ids must be a list'
            }, status=400)
        
        if not notification_ids:
            return JsonResponse({
                'error': 'notification_ids cannot be empty'
            }, status=400)
        
        if len(notification_ids) > 100:  # Reasonable batch size limit
            return JsonResponse({
                'error': 'Too many notification IDs. Maximum 100 per batch.'
            }, status=400)
        
        # Validate and parse UUIDs
        validated_uuids = []
        for notification_id in notification_ids:
            try:
                validated_uuid = uuid.UUID(str(notification_id))
                validated_uuids.append(validated_uuid)
            except (ValueError, TypeError):
                return JsonResponse({
                    'error': f'Invalid UUID format: {notification_id}'
                }, status=400)
        
        # Process acknowledgments in a transaction
        acknowledged = []
        errors = []
        
        with transaction.atomic():
            for notification_uuid in validated_uuids:
                try:
                    # Get the notification
                    try:
                        notification = Notification.objects.get(id=notification_uuid)
                    except Notification.DoesNotExist:
                        errors.append({
                            'notification_id': str(notification_uuid),
                            'error': 'Notification not found'
                        })
                        continue
                    
                    # Check if consumer has a pending notification for this (permission check)
                    # This ensures the consumer is actually subscribed to notifications with matching tags
                    pending_exists = ConsumerNotificationPending.objects.filter(
                        consumer=consumer,
                        notification=notification
                    ).exists()
                    
                    if not pending_exists:
                        errors.append({
                            'notification_id': str(notification_uuid),
                            'error': 'Consumer not subscribed to this notification or already acknowledged'
                        })
                        continue
                    
                    # Create or get the acknowledgment record (idempotent)
                    ack, created = ConsumerNotificationAck.objects.get_or_create(
                        consumer=consumer,
                        notification=notification
                    )
                    
                    # Remove from pending notifications if this acknowledgment was just created
                    if created:
                        ConsumerNotificationPending.objects.filter(
                            consumer=consumer,
                            notification=notification
                        ).delete()
                    
                    # Add to successful acknowledgments
                    acknowledged.append({
                        'notification_id': str(notification_uuid),
                        'acked_at': ack.acknowledged_at.isoformat(),
                        'status': 'success'
                    })
                    
                except Exception as e:
                    # Handle any unexpected errors for individual notifications
                    errors.append({
                        'notification_id': str(notification_uuid),
                        'error': f'Processing error: {str(e)}'
                    })
        
        # Return results
        response_data = {
            'acknowledged': acknowledged,
            'errors': errors,
            'consumer_id': str(consumer.id),
            'total_processed': len(validated_uuids),
            'success_count': len(acknowledged),
            'error_count': len(errors)
        }
        
        # Use 200 OK for partial success, 400 for total failure
        if len(acknowledged) > 0:
            status_code = 200
        else:
            status_code = 400
            
        return JsonResponse(response_data, status=status_code)
        
    except Http404:
        return JsonResponse({
            'error': 'Consumer not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def consumer_status(request, consumer_id):
    """
    GET /api/consumers/{id}/status/
    Get consumer status and health information.
    """
    try:
        # Get the consumer
        consumer = get_object_or_404(Consumer, id=consumer_id)
        
        # Update consumer's last_seen_at
        consumer.save()  # This triggers auto_now on last_seen_at
        
        # Count subscriptions
        subscription_count = consumer.subscriptions.count()
        
        # Count pending notifications
        pending_count = consumer.pending_notifications.count()
        
        # Count total acknowledgments
        ack_count = consumer.acknowledgments.count()
        
        # Get subscription details
        subscriptions = []
        for sub in consumer.subscriptions.all():
            subscriptions.append({
                'tag_type': sub.tag_type,
                'tag_value': sub.tag_value,
                'created_at': sub.created_at.isoformat()
            })
        
        return JsonResponse({
            'consumer_id': str(consumer.id),
            'name': consumer.name,
            'consumer_type': consumer.consumer_type,
            'status': consumer.status,
            'registered_at': consumer.registered_at.isoformat(),
            'last_seen_at': consumer.last_seen_at.isoformat(),
            'metadata': consumer.metadata,
            'stats': {
                'subscription_count': subscription_count,
                'pending_notification_count': pending_count,
                'total_acknowledgments': ack_count
            },
            'subscriptions': subscriptions
        })
        
    except Http404:
        return JsonResponse({
            'error': 'Consumer not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': f'Internal server error: {str(e)}'
        }, status=500)
