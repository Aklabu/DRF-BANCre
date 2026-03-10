from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from utils.response import CustomResponse
from .models import Conversation, Message
from .serializers import (
    ConversationListSerializer,
    ChatSerializer,
    MessageSerializer,
)
from .ai_files.chatbot import get_chat_response


def _get_conversation(user, pk):
    # Helper to fetch a conversation and check ownership in one step
    conversation = get_object_or_404(Conversation, pk=pk)
    if conversation.user != user:
        return None, CustomResponse.error(
            message='You do not have permission to access this conversation.',
            status_code=403,
        )
    return conversation, None


class ChatView(APIView):
    # send a message and get an AI reply in one step
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        if not serializer.is_valid():
            return CustomResponse.error(
                message='Invalid request.',
                errors=serializer.errors,
                status_code=400,
            )

        user_message    = serializer.validated_data['message']
        conversation_id = serializer.validated_data.get('conversation_id')

        # --- Resolve or create conversation ---
        if conversation_id:
            conversation, error = _get_conversation(request.user, conversation_id)
            if error:
                return error
            is_new = False
        else:
            conversation = Conversation.objects.create(user=request.user)
            is_new = True

        is_first_message = is_new or not conversation.messages.exists()

        # Build history from all existing messages (oldest first)
        existing_messages    = conversation.messages.order_by('created_at')
        conversation_history = [
            {'role': msg.role, 'content': msg.content}
            for msg in existing_messages
        ]

        # Persist the user message
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message,
        )

        # Call the AI — this view is the only caller of get_chat_response()
        try:
            result = get_chat_response(user_message, conversation_history)
        except Exception:
            return CustomResponse.error(
                message='AI service is temporarily unavailable. Please try again.',
                status_code=503,
            )

        reply = result['reply']

        # Persist the assistant reply
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=reply,
        )

        # Auto-set title from the first 60 chars of the opening message
        if is_first_message:
            conversation.title = user_message[:60].strip()

        # Touch updated_at on every exchange
        conversation.save(update_fields=['title', 'updated_at'])

        return CustomResponse.success(
            message='Message sent successfully.',
            data={
                'conversation_id': conversation.id,
                'reply':           reply,
            },
            status_code=201,
        )


class ConversationListView(APIView):
    # list all conversations for the user
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = Conversation.objects.filter(user=request.user)
        serializer    = ConversationListSerializer(conversations, many=True)
        return CustomResponse.success(
            message='Conversations retrieved successfully.',
            data=serializer.data,
        )


class ConversationDetailView(APIView):
    # retrieve messages for a specific conversation or delete the conversation
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        conversation, error = _get_conversation(request.user, pk)
        if error:
            return error

        messages   = conversation.messages.order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return CustomResponse.success(
            message='Messages retrieved successfully.',
            data=serializer.data,
        )

    def delete(self, request, pk):
        conversation, error = _get_conversation(request.user, pk)
        if error:
            return error
        conversation.delete()
        return CustomResponse.success(message='Conversation deleted successfully.')