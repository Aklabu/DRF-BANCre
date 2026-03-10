from rest_framework.permissions import BasePermission


class IsConversationOwner(BasePermission):
    message = 'You do not have permission to access this conversation.'

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user