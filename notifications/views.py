from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from utils.response import CustomResponse
from .models import Notification
from .serializers import NotificationSerializer
from .permissions import IsRecipient


class NotificationListView(APIView):
    # list all notifications for the authenticated user
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(recipient=request.user)
        serializer    = NotificationSerializer(notifications, many=True)
        return CustomResponse.success(
            message='Notifications retrieved successfully.',
            data=serializer.data,
        )


class UnreadCountView(APIView):
    # returns unread notification count for badge display
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return CustomResponse.success(
            message='Unread count retrieved successfully.',
            data={'unread_count': count},
        )


class MarkAsReadView(APIView):
    # mark a single notification as read
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk)

        # Only the recipient can mark their own notification as read
        if not IsRecipient().has_object_permission(request, self, notification):
            return CustomResponse.error(
                message='You do not have permission to access this notification.',
                status_code=403,
            )

        notification.is_read = True
        notification.save(update_fields=['is_read'])

        serializer = NotificationSerializer(notification)
        return CustomResponse.success(
            message='Notification marked as read.',
            data=serializer.data,
        )


class MarkAllAsReadView(APIView):
    # mark all unread notifications as read in one bulk update
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        # Use bulk update for efficiency — never loop and save individually
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)

        return CustomResponse.success(
            message=f'{updated} notification(s) marked as read.',
            data={'updated_count': updated},
        )


class DeleteNotificationView(APIView):
    # delete a single notification
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk)

        # Only the recipient can delete their own notification
        if not IsRecipient().has_object_permission(request, self, notification):
            return CustomResponse.error(
                message='You do not have permission to delete this notification.',
                status_code=403,
            )

        notification.delete()
        return CustomResponse.success(message='Notification deleted successfully.')


class ClearAllNotificationsView(APIView):
    # delete all notifications for the authenticated user
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        # Single queryset delete — never loop and delete individually
        deleted_count, _ = Notification.objects.filter(recipient=request.user).delete()
        return CustomResponse.success(
            message=f'{deleted_count} notification(s) cleared.',
            data={'deleted_count': deleted_count},
        )