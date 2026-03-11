from django.contrib import admin
from .models import Notification


# Custom admin action — bulk mark selected notifications as read
@admin.action(description='Mark selected notifications as read')
def mark_as_read(modeladmin, request, queryset):
    queryset.update(is_read=True)


# Custom admin action — bulk delete selected notifications
@admin.action(description='Delete selected notifications')
def delete_notifications(modeladmin, request, queryset):
    queryset.delete()


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display   = ['id', 'recipient', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter    = ['notification_type', 'is_read', 'created_at']
    search_fields  = ['recipient__email', 'title', 'message']
    ordering       = ['-created_at']
    readonly_fields = ['created_at']
    actions        = [mark_as_read, delete_notifications]

    fieldsets = (
        # Core notification fields
        ('Notification', {
            'fields': ('recipient', 'notification_type', 'title', 'message', 'is_read'),
        }),
        # Reference IDs for deep linking — all optional
        ('Reference IDs', {
            'fields': ('memorandum_id', 'loan_request_id', 'quote_id'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    )