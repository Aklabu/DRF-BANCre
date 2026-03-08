from django.urls import path
from .views import (
    LoanRequestListCreateView,
    LoanRequestDetailView,
    LoanQuoteListCreateView,
    LenderQuoteListView,
    LoanQuoteDetailView,
    AcceptQuoteView,
    DeclineQuoteView,
    LenderDashboardView,
    SponsorDashboardView,
)

app_name = 'loans'

urlpatterns = [
    # Loan Requests
    path('requests/',        LoanRequestListCreateView.as_view(), name='loan-request-list-create'),
    path('requests/<int:pk>/', LoanRequestDetailView.as_view(),  name='loan-request-detail'),

    # Quotes scoped to a loan request
    path('requests/<int:pk>/quotes/', LoanQuoteListCreateView.as_view(), name='loan-quote-list-create'),

    # Standalone quote endpoints
    path('quotes/',                        LenderQuoteListView.as_view(),  name='lender-quote-list'),
    path('quotes/<int:quote_id>/',         LoanQuoteDetailView.as_view(),  name='loan-quote-detail'),
    path('quotes/<int:quote_id>/accept/',  AcceptQuoteView.as_view(),      name='loan-quote-accept'),
    path('quotes/<int:quote_id>/decline/', DeclineQuoteView.as_view(),     name='loan-quote-decline'),

    # Dashboards
    path('dashboard/lender/',  LenderDashboardView.as_view(),  name='lender-dashboard'),
    path('dashboard/sponsor/', SponsorDashboardView.as_view(), name='sponsor-dashboard'),
]