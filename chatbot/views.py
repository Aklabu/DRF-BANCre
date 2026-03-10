from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from utils.response import CustomResponse
from .models import Conversation, Message
from .serializers import (
    ConversationListSerializer,
    SendMessageSerializer,
    MessageSerializer,
)
from .permissions import IsConversationOwner

# Import the AI entry point — the view is the only layer that calls this
from .ai_files.chatbot import get_chat_response


def _get_conversation(user, pk):
    # Helper function to fetch a conversation and check ownership
    conversation = get_object_or_404(Conversation, pk=pk)
    if conversation.user != user:
        return None, CustomResponse.error(
            message='You do not have permission to access this conversation.',
            status_code=403,
        )
    return conversation, None


class ConversationListCreateView(APIView):
    # GET  — List all conversations for the authenticated user
    # CREATE — Start a new conversation 
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = Conversation.objects.filter(user=request.user)
        serializer = ConversationListSerializer(conversations, many=True)
        return CustomResponse.success(
            message='Conversations retrieved successfully.',
            data=serializer.data,
        )

    def post(self, request):
        conversation = Conversation.objects.create(user=request.user)
        serializer = ConversationListSerializer(conversation)
        return CustomResponse.success(
            message='Conversation created successfully.',
            data=serializer.data,
            status_code=201,
        )


class ConversationDeleteView(APIView):
    # Delete a conversation and all its messages
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        conversation, error = _get_conversation(request.user, pk)
        if error:
            return error
        conversation.delete()
        return CustomResponse.success(message='Conversation deleted successfully.')


class MessageListCreateView(APIView):
    # GET  — Return full message history for a conversation (oldest first).
    # POST — Send a user message, get an AI reply, and persist both.
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        conversation, error = _get_conversation(request.user, pk)
        if error:
            return error

        messages = conversation.messages.order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return CustomResponse.success(
            message='Messages retrieved successfully.',
            data=serializer.data,
        )

    def post(self, request, pk):
        conversation, error = _get_conversation(request.user, pk)
        if error:
            return error

        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return CustomResponse.error(
                message='Invalid request.',
                errors=serializer.errors,
                status_code=400,
            )

        user_message = serializer.validated_data['message']
        is_first_message = not conversation.messages.exists()

        # Build conversation history from all existing messages (oldest first)
        existing_messages = conversation.messages.order_by('created_at')
        conversation_history = [
            {'role': msg.role, 'content': msg.content}
            for msg in existing_messages
        ]

        # Persist the user's message
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message,
        )

        # Call the AI — the view is the only caller of get_chat_response()
        try:
            result = get_chat_response(user_message, conversation_history)
        except Exception:
            return CustomResponse.error(
                message='AI service is temporarily unavailable. Please try again.',
                status_code=503,
            )

        reply = result['reply']

        # Persist the assistant's reply
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=reply,
        )

        # Auto-generate title from the first 60 characters of the opening message
        if is_first_message:
            conversation.title = user_message[:60].strip()

        # Touch updated_at on every new message
        conversation.save(update_fields=['title', 'updated_at'])

        return CustomResponse.success(
            message='Message sent successfully.',
            data={
                'conversation_id': conversation.id,
                'reply': reply,
            },
            status_code=201,
        )