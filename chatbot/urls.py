from django.urls import path
from .views import (
    ConversationListCreateView,
    ConversationDeleteView,
    MessageListCreateView,
)

app_name = 'chatbot'

urlpatterns = [
    # Conversation management
    path('conversations/',         ConversationListCreateView.as_view(), name='conversation-list-create'),
    path('conversations/<int:pk>/', ConversationDeleteView.as_view(),    name='conversation-delete'),

    # Message history and sending
    path('conversations/<int:pk>/messages/', MessageListCreateView.as_view(), name='message-list-create'),
]