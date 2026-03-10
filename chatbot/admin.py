from django.contrib import admin
from .models import Conversation, Message


# Admin classes to manage Conversations and Messages in the Django admin interface
class MessageInline(admin.TabularInline):
    model           = Message
    extra           = 0
    readonly_fields = ['role', 'content', 'created_at']
    fields          = ['role', 'content', 'created_at']
    ordering        = ['created_at']
    can_delete      = False


@admin.register(Conversation)
# Admin interface for managing conversations, with inline display of messages
class ConversationAdmin(admin.ModelAdmin):
    list_display    = ['id', 'user', 'title', 'created_at', 'updated_at']
    list_filter     = ['created_at', 'updated_at']
    search_fields   = ['user__email', 'title']
    ordering        = ['-updated_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines         = [MessageInline]

    fieldsets = (
        (None,         {'fields': ('user', 'title')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Message)
# Admin interface for managing individual messages
class MessageAdmin(admin.ModelAdmin):
    list_display    = ['id', 'conversation', 'role', 'content_preview', 'created_at']
    list_filter     = ['role', 'created_at']
    search_fields   = ['conversation__user__email', 'content']
    ordering        = ['-created_at']
    readonly_fields = ['created_at']

    def content_preview(self, obj):
        return obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
    content_preview.short_description = 'Content'