#!/usr/bin/env python
"""
Create an inactive consumer for testing access control.
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital.settings')
django.setup()

from core.models import Consumer

def create_inactive_consumer():
    # Create an inactive consumer
    consumer = Consumer.objects.create(
        name="Inactive Test Consumer",
        consumer_type='mobile',
        status='inactive',  # Make it inactive
        metadata={'test': 'true'}
    )
    
    print(f"Created inactive consumer: {consumer.id}")
    return consumer.id

if __name__ == "__main__":
    consumer_id = create_inactive_consumer()