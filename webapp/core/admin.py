from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Room

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role and Room', {'fields': ('role', 'assigned_room')}),
    )
    list_display = ('username', 'email', 'role', 'assigned_room')
    list_filter = ('role',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'timer_seconds', 'timer_started_at')
    search_fields = ('name',)
