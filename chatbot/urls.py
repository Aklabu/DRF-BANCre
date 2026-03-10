from django.urls import path
from .views import (
    ChatView,
    ConversationListView,
    ConversationDetailView,
)

app_name = 'chatbot'

urlpatterns = [
    # Core chat — auto-creates or continues a conversation
    path('chat/', ChatView.as_view(), name='chat'),

    # Conversation history list
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),

    # Message history for a conversation
    path('conversations/<int:pk>/messages/', ConversationDetailView.as_view(), name='conversation-messages'),

    # Delete a conversation (and all its messages)
    path('conversations/<int:pk>/',          ConversationDetailView.as_view(), name='conversation-delete'),
]