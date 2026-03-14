from django.db.models import Count, Sum
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from utils.response import CustomResponse
from properties.models import Property, PropertyDocument
from loans.models import LoanRequest, LoanQuote
from .permissions import IsSponsor, IsLender


class SponsorDashboardView(APIView):
    # returns aggregated stats for the authenticated sponsor
    permission_classes = [IsAuthenticated, IsSponsor]

    def get(self, request):
        user = request.user

        # count all properties owned by this sponsor
        total_properties = Property.objects.filter(sponsor=user).count()

        # count all documents across all properties owned by this sponsor
        documents_count = PropertyDocument.objects.filter(property__sponsor=user).count()

        # count all quotes received across all loan requests owned by this sponsor
        quotes_received = LoanQuote.objects.filter(loan_request__sponsor=user).count()

        # sum requested_amount across all loan requests by this sponsor — coerce None to 0
        portfolio_value = (
            LoanRequest.objects
            .filter(sponsor=user)
            .aggregate(total=Sum('requested_amount'))['total']
        ) or 0

        return CustomResponse.success(
            message='Sponsor dashboard stats retrieved successfully.',
            data={
                'total_properties': total_properties,
                'quotes_received':  quotes_received,
                'documents_count':  documents_count,
                'portfolio_value':  portfolio_value,
            },
        )


class LenderDashboardView(APIView):
    # returns aggregated stats for the authenticated lender
    permission_classes = [IsAuthenticated, IsLender]

    def get(self, request):
        user = request.user

        # global count of all active loan requests — visible to all lenders
        active_requests = LoanRequest.objects.filter(status='Active').count()

        # count all quotes ever submitted by this lender
        quotes_provided = LoanQuote.objects.filter(lender=user).count()

        # count quotes submitted by this lender that are currently under review
        pending_review = LoanQuote.objects.filter(lender=user, status='Under Review').count()

        # count quotes submitted by this lender that have been accepted
        accepted_quotes = LoanQuote.objects.filter(lender=user, status='Accepted').count()

        return CustomResponse.success(
            message='Lender dashboard stats retrieved successfully.',
            data={
                'active_requests': active_requests,
                'quotes_provided': quotes_provided,
                'pending_review':  pending_review,
                'accepted_quotes': accepted_quotes,
            },
        )