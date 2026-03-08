from rest_framework.permissions import BasePermission


class IsSponsor(BasePermission):
    message = 'Only Sponsor accounts can perform this action.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.customer_type == 'Sponsor'
        )


class IsLender(BasePermission):
    message = 'Only Lender accounts can perform this action.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.customer_type == 'Lender'
        )


class IsSponsorOrLender(BasePermission):
    message = 'Only Sponsor or Lender accounts can perform this action.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.customer_type in ('Sponsor', 'Lender')
        )


class IsLoanRequestOwner(BasePermission):
    message = 'You do not have permission to modify this loan request.'

    def has_object_permission(self, request, view, obj):
        return obj.sponsor == request.user


class IsQuoteOwner(BasePermission):
    message = 'You do not have permission to modify this quote.'

    def has_object_permission(self, request, view, obj):
        return obj.lender == request.user


class CanViewQuote(BasePermission):
    # Both the owning lender and the sponsor of the associated loan request can view the quote details.
    message = 'You do not have permission to view this quote.'

    def has_object_permission(self, request, view, obj):
        return (
            obj.lender == request.user
            or obj.loan_request.sponsor == request.user
        )