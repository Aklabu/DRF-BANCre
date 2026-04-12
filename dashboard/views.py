from django.db.models import Count, Sum, Avg, Q
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


class LenderQuoteStatsView(APIView):
    # returns quote-level stats for the authenticated lender
    # mirrors the data visible on GET /api/loans/quotes/
    permission_classes = [IsAuthenticated, IsLender]

    def get(self, request):
        user = request.user

        # base queryset — all quotes submitted by this lender
        quotes = LoanQuote.objects.filter(lender=user)

        # total number of quotes ever submitted by this lender
        total_quotes = quotes.count()

        # quotes still waiting on sponsor action — neither accepted nor declined
        under_review_quotes = quotes.filter(status='Under Review').count()

        # quotes the sponsor has accepted
        accepted_quotes = quotes.filter(status='Accepted').count()

        # sum of loan_amount across all submitted quotes — coerce None to 0
        total_value = quotes.aggregate(total=Sum('loan_amount'))['total'] or 0

        return CustomResponse.success(
            message='Lender quote stats retrieved successfully.',
            data={
                'total_quotes':       total_quotes,
                'under_review_quotes': under_review_quotes,
                'accepted_quotes':    accepted_quotes,
                'total_value':        total_value,
            },
        )


class LenderPropertyStatsView(APIView):
    # returns property-level stats for the authenticated lender
    # mirrors the properties visible on GET /api/properties/map/
    permission_classes = [IsAuthenticated, IsLender]

    def get(self, request):
        # total number of properties visible on the map — same queryset as PropertyMapView
        total_properties = Property.objects.count()

        # sum of requested_amount across all active loan requests linked to these properties
        # a property may have multiple loan requests — sum all of them
        total_loan_value = (
            LoanRequest.objects
            .filter(status='Active')
            .aggregate(total=Sum('requested_amount'))['total']
        ) or 0

        # average loan amount = total loan value / total properties
        # guard against division by zero if no properties exist
        if total_properties > 0:
            average_loan_amount = round(total_loan_value / total_properties, 2)
        else:
            average_loan_amount = 0

        return CustomResponse.success(
            message='Lender property stats retrieved successfully.',
            data={
                'total_properties':   total_properties,
                'total_loan_value':   total_loan_value,
                'average_loan_amount': average_loan_amount,
            },
        )