from django.urls import path
from .views import (
    SponsorDashboardView,
    LenderDashboardView,
    LenderQuoteStatsView,
    LenderPropertyStatsView,
)

app_name = 'dashboard'

urlpatterns = [
    path('sponsor/',                SponsorDashboardView.as_view(),      name='sponsor-dashboard'),
    path('lender/',                 LenderDashboardView.as_view(),        name='lender-dashboard'),
    path('lender/quote-stats/',     LenderQuoteStatsView.as_view(),       name='lender-quote-stats'),
    path('lender/property-stats/',  LenderPropertyStatsView.as_view(),    name='lender-property-stats'),
]