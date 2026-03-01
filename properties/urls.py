from django.urls import path
from .views import (
    PropertyListCreateView,
    PropertyDetailView,
    PropertyDocumentListCreateView,
    PropertyDocumentDeleteView,
    PropertyMapView,
)

app_name = 'properties'

urlpatterns = [
    # Map endpoint — must come before {id}/ to avoid conflict
    path('map/', PropertyMapView.as_view(), name='property-map'),

    # Property CRUD
    path('', PropertyListCreateView.as_view(), name='property-list-create'),
    path('<int:pk>/', PropertyDetailView.as_view(), name='property-detail'),

    # Document endpoints
    path('<int:pk>/documents/', PropertyDocumentListCreateView.as_view(), name='property-document-list-create'),
    path('<int:pk>/documents/<int:doc_id>/', PropertyDocumentDeleteView.as_view(), name='property-document-delete'),
]