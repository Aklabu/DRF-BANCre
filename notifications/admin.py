from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Notification, NotificationPreference


@admin.action(description='Mark selected notifications as read')
def mark_as_read(modeladmin, request, queryset):
    queryset.update(is_read=True)


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display    = ['id', 'recipient', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter     = ['notification_type', 'is_read']
    search_fields   = ['recipient__email', 'title']
    readonly_fields = ['created_at']
    actions         = [mark_as_read]


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(ModelAdmin):
    list_display    = ['user', 'quote_emails_enabled', 'updated_at']
    search_fields   = ['user__email']
    readonly_fields = ['updated_at']