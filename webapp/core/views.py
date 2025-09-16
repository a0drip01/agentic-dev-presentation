from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from .models import Consumer, ConsumerSubscription
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
    """
    return JsonResponse({
        'status': 'not_implemented',
        'message': f'Notification polling endpoint - placeholder',
        'endpoint': f'GET /api/consumers/{consumer_id}/notifications/',
        'consumer_id': str(consumer_id)
    }, status=501)


@csrf_exempt
@require_http_methods(["POST"])
def acknowledge_notifications(request, consumer_id):
    """
    POST /api/consumers/{id}/notifications/ack/
    Acknowledge one or more notifications as processed.
    """
    return JsonResponse({
        'status': 'not_implemented',
        'message': f'Notification acknowledgment endpoint - placeholder',
        'endpoint': f'POST /api/consumers/{consumer_id}/notifications/ack/',
        'consumer_id': str(consumer_id)
    }, status=501)


@csrf_exempt
@require_http_methods(["GET"])
def consumer_status(request, consumer_id):
    """
    GET /api/consumers/{id}/status/
    Get consumer status and health information.
    """
    return JsonResponse({
        'status': 'not_implemented',
        'message': f'Consumer status endpoint - placeholder',
        'endpoint': f'GET /api/consumers/{consumer_id}/status/',
        'consumer_id': str(consumer_id)
    }, status=501)
