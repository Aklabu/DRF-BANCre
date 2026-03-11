from rest_framework.permissions import BasePermission


class IsRecipient(BasePermission):
    # Only the recipient of the notification can access it
    message = 'You do not have permission to access this notification.'

    def has_object_permission(self, request, view, obj):
        return obj.recipient == request.user