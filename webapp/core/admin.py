from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Room, Notification, NotificationRead, WebhookSubscription,
    Consumer, ConsumerSubscription, ConsumerNotificationAck, ConsumerNotificationPending
)

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


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'timestamp', 'message_preview')
    list_filter = ('room', 'timestamp')
    search_fields = ('message', 'room__name')
    readonly_fields = ('id', 'timestamp')
    
    def message_preview(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = "Message Preview"


@admin.register(NotificationRead)
class NotificationReadAdmin(admin.ModelAdmin):
    list_display = ('notification', 'user', 'read_at')
    list_filter = ('read_at', 'user__role')
    search_fields = ('notification__id', 'user__username')


@admin.register(WebhookSubscription)
class WebhookSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('url', 'room', 'created_at')
    list_filter = ('room', 'created_at')
    search_fields = ('url', 'room__name')


@admin.register(Consumer)
class ConsumerAdmin(admin.ModelAdmin):
    list_display = ('name', 'consumer_type', 'status', 'registered_at', 'last_seen_at')
    list_filter = ('consumer_type', 'status', 'registered_at')
    search_fields = ('name', 'id')
    readonly_fields = ('id', 'registered_at', 'last_seen_at')
    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'consumer_type', 'status')
        }),
        ('Timestamps', {
            'fields': ('registered_at', 'last_seen_at')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )


class ConsumerSubscriptionInline(admin.TabularInline):
    model = ConsumerSubscription
    extra = 1


@admin.register(ConsumerSubscription)
class ConsumerSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('consumer', 'tag_type', 'tag_value', 'created_at')
    list_filter = ('tag_type', 'created_at')
    search_fields = ('consumer__name', 'tag_value')


@admin.register(ConsumerNotificationAck)
class ConsumerNotificationAckAdmin(admin.ModelAdmin):
    list_display = ('consumer', 'notification', 'acknowledged_at')
    list_filter = ('acknowledged_at', 'consumer__consumer_type')
    search_fields = ('consumer__name', 'notification__id')
    readonly_fields = ('acknowledged_at',)


@admin.register(ConsumerNotificationPending)
class ConsumerNotificationPendingAdmin(admin.ModelAdmin):
    list_display = ('consumer', 'notification', 'created_at')
    list_filter = ('created_at', 'consumer__consumer_type')
    search_fields = ('consumer__name', 'notification__id')
    readonly_fields = ('created_at',)


# Add inline subscriptions to Consumer admin
ConsumerAdmin.inlines = [ConsumerSubscriptionInline]
