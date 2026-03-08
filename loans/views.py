from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Min
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from utils.response import CustomResponse
from .models import LoanRequest, LoanQuote
from .serializers import (
    LoanRequestCreateSerializer,
    LoanRequestListSerializer,
    LoanRequestDetailSerializer,
    LoanRequestUpdateSerializer,
    LoanQuoteCreateSerializer,
    LoanQuoteSerializer,
    LoanQuoteUpdateSerializer,
    LenderDashboardRequestSerializer,
    SponsorQuoteCardSerializer,
)
from .permissions import (
    IsSponsor, IsLender, IsSponsorOrLender,
    IsLoanRequestOwner, IsQuoteOwner, CanViewQuote,
)
from .notifications import (
    notify_sponsor_new_quote,
    notify_lender_quote_accepted,
    notify_lender_quote_declined,
)


# Loan Request Views for Sponsors and Lenders
class LoanRequestListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsSponsorOrLender]

    def get(self, request):
        user = request.user
        if user.customer_type == 'Sponsor':
            queryset = LoanRequest.objects.filter(sponsor=user).select_related('property')
        else:
            # Lenders see all Active requests
            queryset = LoanRequest.objects.filter(status='Active').select_related('property')

        serializer = LoanRequestListSerializer(queryset, many=True, context={'request': request})
        return CustomResponse.success(
            message='Loan requests retrieved successfully.',
            data=serializer.data,
        )

    def post(self, request):
        # Only sponsors can create loan requests
        if request.user.customer_type != 'Sponsor':
            return CustomResponse.error(
                message='Only Sponsor accounts can create loan requests.',
                status_code=403,
            )
        serializer = LoanRequestCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            loan_request = serializer.save(sponsor=request.user, status='Active')
            out = LoanRequestDetailSerializer(loan_request, context={'request': request})
            return CustomResponse.success(
                message='Loan request created successfully.',
                data=out.data,
                status_code=status.HTTP_201_CREATED,
            )
        return CustomResponse.error(
            message='Loan request creation failed.',
            errors=serializer.errors,
            status_code=400,
        )


class LoanRequestDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSponsorOrLender]

    def _get_request(self, pk):
        return get_object_or_404(
            LoanRequest.objects.select_related('property', 'sponsor'),
            pk=pk,
        )

    def get(self, request, pk):
        loan_request = self._get_request(pk)
        # Lenders can only view Active requests
        if request.user.customer_type == 'Lender' and loan_request.status != 'Active':
            return CustomResponse.error(
                message='Loan request not found.',
                status_code=404,
            )
        serializer = LoanRequestDetailSerializer(loan_request, context={'request': request})
        return CustomResponse.success(
            message='Loan request retrieved successfully.',
            data=serializer.data,
        )

    def patch(self, request, pk):
        if request.user.customer_type != 'Sponsor':
            return CustomResponse.error(message='Only Sponsors can update loan requests.', status_code=403)
        loan_request = self._get_request(pk)
        if not IsLoanRequestOwner().has_object_permission(request, self, loan_request):
            return CustomResponse.error(message='You do not have permission to update this loan request.', status_code=403)
        serializer = LoanRequestUpdateSerializer(loan_request, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            out = LoanRequestDetailSerializer(loan_request, context={'request': request})
            return CustomResponse.success(message='Loan request updated successfully.', data=out.data)
        return CustomResponse.error(message='Update failed.', errors=serializer.errors, status_code=400)

    def delete(self, request, pk):
        if request.user.customer_type != 'Sponsor':
            return CustomResponse.error(message='Only Sponsors can delete loan requests.', status_code=403)
        loan_request = self._get_request(pk)
        if not IsLoanRequestOwner().has_object_permission(request, self, loan_request):
            return CustomResponse.error(message='You do not have permission to delete this loan request.', status_code=403)
        loan_request.delete()
        return CustomResponse.success(message='Loan request deleted successfully.')


# Loan Quote Views for Sponsors and Lenders
class LoanQuoteListCreateView(APIView):
    # GET  — Sponsor-only: all quotes on a specific loan request.
    # POST — Lender-only: submit a quote on a specific loan request.
    permission_classes = [IsAuthenticated]

    def _get_loan_request(self, pk):
        return get_object_or_404(LoanRequest, pk=pk)

    def get(self, request, pk):
        if request.user.customer_type != 'Sponsor':
            return CustomResponse.error(message='Only Sponsors can view quotes on a loan request.', status_code=403)
        loan_request = self._get_loan_request(pk)
        if not IsLoanRequestOwner().has_object_permission(request, self, loan_request):
            return CustomResponse.error(message='You do not have permission to access this loan request.', status_code=403)
        quotes = loan_request.quotes.select_related('lender').all()
        serializer = LoanQuoteSerializer(quotes, many=True, context={'request': request})
        return CustomResponse.success(message='Quotes retrieved successfully.', data=serializer.data)

    def post(self, request, pk):
        if request.user.customer_type != 'Lender':
            return CustomResponse.error(message='Only Lenders can submit quotes.', status_code=403)
        loan_request = self._get_loan_request(pk)
        if loan_request.status != 'Active':
            return CustomResponse.error(message='Quotes can only be submitted on Active loan requests.', status_code=400)
        serializer = LoanQuoteCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            quote = serializer.save(
                loan_request=loan_request,
                lender=request.user,
                status='Submitted',
            )
            notify_sponsor_new_quote(loan_request, quote)
            out = LoanQuoteSerializer(quote, context={'request': request})
            return CustomResponse.success(
                message='Quote submitted successfully.',
                data=out.data,
                status_code=status.HTTP_201_CREATED,
            )
        return CustomResponse.error(message='Quote submission failed.', errors=serializer.errors, status_code=400)


class LenderQuoteListView(APIView):
    # List all quotes submitted by the lender across all loan requests.
    permission_classes = [IsAuthenticated, IsLender]

    def get(self, request):
        quotes = LoanQuote.objects.filter(lender=request.user).select_related('loan_request__property')
        serializer = LoanQuoteSerializer(quotes, many=True, context={'request': request})
        return CustomResponse.success(message='Your quotes retrieved successfully.', data=serializer.data)


class LoanQuoteDetailView(APIView):
    # Detail view for a specific quote.
    permission_classes = [IsAuthenticated]

    def _get_quote(self, quote_id):
        return get_object_or_404(
            LoanQuote.objects.select_related('lender', 'loan_request__sponsor', 'loan_request__property'),
            pk=quote_id,
        )

    def get(self, request, quote_id):
        quote = self._get_quote(quote_id)
        if not CanViewQuote().has_object_permission(request, self, quote):
            return CustomResponse.error(message='You do not have permission to view this quote.', status_code=403)
        serializer = LoanQuoteSerializer(quote, context={'request': request})
        return CustomResponse.success(message='Quote retrieved successfully.', data=serializer.data)

    def patch(self, request, quote_id):
        if request.user.customer_type != 'Lender':
            return CustomResponse.error(message='Only Lenders can update quotes.', status_code=403)
        quote = self._get_quote(quote_id)
        if not IsQuoteOwner().has_object_permission(request, self, quote):
            return CustomResponse.error(message='You do not have permission to update this quote.', status_code=403)
        serializer = LoanQuoteUpdateSerializer(quote, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            out = LoanQuoteSerializer(quote, context={'request': request})
            return CustomResponse.success(message='Quote updated successfully.', data=out.data)
        return CustomResponse.error(message='Quote update failed.', errors=serializer.errors, status_code=400)


class AcceptQuoteView(APIView):
    # Sponsor accepts a specific quote
    permission_classes = [IsAuthenticated, IsSponsor]

    def post(self, request, quote_id):
        quote = get_object_or_404(
            LoanQuote.objects.select_related('loan_request__sponsor', 'loan_request__property'),
            pk=quote_id,
        )
        loan_request = quote.loan_request

        if loan_request.sponsor != request.user:
            return CustomResponse.error(message='You do not have permission to accept this quote.', status_code=403)
        if loan_request.status == 'Closed':
            return CustomResponse.error(message='This loan request is already closed.', status_code=400)

        # Accept this quote
        quote.status = 'Accepted'
        quote.save(update_fields=['status', 'updated_at'])
        notify_lender_quote_accepted(quote)

        # Decline all other quotes on the same loan request
        other_quotes = LoanQuote.objects.filter(
            loan_request=loan_request,
        ).exclude(pk=quote.pk)

        for other in other_quotes:
            other.status = 'Declined'
            other.save(update_fields=['status', 'updated_at'])
            notify_lender_quote_declined(other)

        # Close the loan request
        loan_request.status = 'Closed'
        loan_request.save(update_fields=['status', 'updated_at'])

        serializer = LoanQuoteSerializer(quote, context={'request': request})
        return CustomResponse.success(message='Quote accepted. Loan request is now closed.', data=serializer.data)


class DeclineQuoteView(APIView):
    # Sponsor declines a specific quote. This does not affect the loan request status or other quotes.
    permission_classes = [IsAuthenticated, IsSponsor]

    def post(self, request, quote_id):
        quote = get_object_or_404(
            LoanQuote.objects.select_related('loan_request__sponsor'),
            pk=quote_id,
        )
        if quote.loan_request.sponsor != request.user:
            return CustomResponse.error(message='You do not have permission to decline this quote.', status_code=403)
        if quote.status in ('Accepted', 'Declined'):
            return CustomResponse.error(message=f'Quote is already {quote.status}.', status_code=400)

        quote.status = 'Declined'
        quote.save(update_fields=['status', 'updated_at'])
        notify_lender_quote_declined(quote)

        serializer = LoanQuoteSerializer(quote, context={'request': request})
        return CustomResponse.success(message='Quote declined successfully.', data=serializer.data)


# Dashboard Views for Sponsors and Lenders
class LenderDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsLender]

    def get(self, request):
        user = request.user

        active_requests  = LoanRequest.objects.filter(status='Active').count()
        quotes_provided  = LoanQuote.objects.filter(lender=user).count()
        pending_review   = LoanQuote.objects.filter(lender=user, status='Under Review').count()
        accepted_quotes  = LoanQuote.objects.filter(lender=user, status='Accepted').count()

        loan_requests = LoanRequest.objects.filter(status='Active').select_related('property')
        requests_serializer = LenderDashboardRequestSerializer(loan_requests, many=True, context={'request': request})

        data = {
            'header_stats': {
                'active_requests': active_requests,
                'quotes_provided': quotes_provided,
                'pending_review':  pending_review,
                'accepted_quotes': accepted_quotes,
            },
            'available_loan_requests': requests_serializer.data,
        }
        return CustomResponse.success(message='Lender dashboard retrieved successfully.', data=data)


class SponsorDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsSponsor]

    def get(self, request):
        user = request.user

        total_properties = user.properties.count()
        documents_count  = sum(p.documents.count() for p in user.properties.all())
        portfolio_value  = (
            LoanRequest.objects.filter(sponsor=user, status='Active')
            .aggregate(total=Sum('requested_amount'))['total'] or 0
        )

        # All quotes across the sponsor's loan requests
        all_quotes = LoanQuote.objects.filter(
            loan_request__sponsor=user,
        ).select_related('loan_request__property')

        quotes_received = all_quotes.count()

        # Card view data
        quote_serializer = SponsorQuoteCardSerializer(all_quotes, many=True, context={'request': request})
        quote_list = quote_serializer.data

        # Comparison stats
        best_rate    = all_quotes.aggregate(best=Min('interest_rate'))['best']
        highest_ltv  = all_quotes.aggregate(best=Min('max_as_is_ltv'))['best']

        data = {
            'header_stats': {
                'total_properties': total_properties,
                'quotes_received':  quotes_received,
                'documents_count':  documents_count,
                'portfolio_value':  portfolio_value,
            },
            'quote_card_view': quote_list,
            'quote_comparison': {
                'total_quotes': quotes_received,
                'best_rate':    best_rate,
                'highest_ltv':  highest_ltv,
                'quotes':       quote_list,
            },
        }
        return CustomResponse.success(message='Sponsor dashboard retrieved successfully.', data=data)