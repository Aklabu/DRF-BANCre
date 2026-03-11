from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model  = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'is_read',
            'created_at',
            # Reference IDs for frontend deep linking
            'memorandum_id',
            'loan_request_id',
            'quote_id',
        ]
        read_only_fields = fields