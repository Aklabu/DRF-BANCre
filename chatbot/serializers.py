from rest_framework import serializers
from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Message
        fields = ['id', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'role', 'created_at']


class ConversationListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at']


class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model  = Conversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'messages']


class SendMessageSerializer(serializers.Serializer):
    message = serializers.CharField(allow_blank=False, trim_whitespace=True)