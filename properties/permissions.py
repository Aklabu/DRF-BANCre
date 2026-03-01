from rest_framework.permissions import BasePermission


class IsSponsor(BasePermission):
    # Allow access only to users with customer_type == 'Sponsor'.
    message = 'Only Sponsor accounts can perform this action.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.customer_type == 'Sponsor'
        )


class IsLender(BasePermission):
    # Allow access only to users with customer_type == 'Lender'.
    message = 'Only Lender accounts can access the map.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.customer_type == 'Lender'
        )


class IsPropertyOwner(BasePermission):
    # Allow access only to the sponsor who owns the property.
    message = 'You do not have permission to modify this property.'

    def has_object_permission(self, request, view, obj):
        # obj is a Property instance
        return obj.sponsor == request.user