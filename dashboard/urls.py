from django.urls import path
from .views import SponsorDashboardView, LenderDashboardView

app_name = 'dashboard'

urlpatterns = [
    path('sponsor/', SponsorDashboardView.as_view(), name='sponsor-dashboard'),
    path('lender/',  LenderDashboardView.as_view(),  name='lender-dashboard'),
]