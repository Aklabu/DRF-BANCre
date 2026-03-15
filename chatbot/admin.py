from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import Conversation, Message


class MessageInline(TabularInline):
    model           = Message
    extra           = 0
    readonly_fields = ['role', 'content', 'created_at']
    fields          = ['role', 'content', 'created_at']
    ordering        = ['created_at']
    can_delete      = False


@admin.register(Conversation)
class ConversationAdmin(ModelAdmin):
    list_display    = ['id', 'user', 'title', 'created_at', 'updated_at']
    search_fields   = ['user__email', 'title']
    readonly_fields = ['created_at', 'updated_at']
    inlines         = [MessageInline]


@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display    = ['id', 'conversation', 'role', 'created_at']
    list_filter     = ['role']
    search_fields   = ['conversation__user__email']
    readonly_fields = ['created_at']