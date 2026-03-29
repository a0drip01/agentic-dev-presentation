"""
UUID threading fix for Django database backend.

This module provides a monkey patch to fix an issue where Django's database
backend tries to call .replace() on UUID objects in thread identifiers.
"""

import threading
from uuid import UUID
from django.apps import AppConfig


def patch_django_db_base():
    """Patch Django's database base module to handle UUID objects safely."""
    try:
        from django.db.backends.base import base
        
        # Store original method
        if not hasattr(base, '_original_get_thread_id'):
            base._original_get_thread_id = getattr(base.BaseDatabaseWrapper, '_get_thread_id', None)
        
        def safe_get_thread_id(self):
            """Safe version of _get_thread_id that handles UUID objects."""
            try:
                thread_ident = threading.get_ident()
                if isinstance(thread_ident, UUID):
                    return str(thread_ident).replace("-", "")
                return str(thread_ident).replace("-", "")
            except Exception as e:
                # Fallback to a safe default
                return str(id(threading.current_thread())).replace("-", "")
        
        # Patch the method
        base.BaseDatabaseWrapper._get_thread_id = safe_get_thread_id
        
        print("✅ Applied Django database backend UUID fix")
        return True
        
    except Exception as e:
        print(f"❌ Failed to apply Django database backend fix: {e}")
        return False


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """Apply monkey patch when app is ready."""
        patch_django_db_base()
        print("✅ Core app ready with UUID threading fix")
