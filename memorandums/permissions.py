from rest_framework.permissions import BasePermission


class IsSponsor(BasePermission):
    message = 'Only Sponsor accounts can perform this action.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.customer_type == 'Sponsor'
        )


class IsMemorandumOwner(BasePermission):
    message = 'You do not have permission to access this memorandum.'

    def has_object_permission(self, request, view, obj):
        return obj.sponsor == request.user