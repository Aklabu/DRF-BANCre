from django.urls import path
from .views import (
    PropertyListCreateView,
    PropertyDetailView,
    PropertyDocumentListCreateView,
    PropertyDocumentDeleteView,
    PropertyMapView,
    PropertyChatView,
    PropertyChatSessionListView,
    PropertyChatSessionDetailView,
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
    path('<int:pk>/chat/', PropertyChatView.as_view(), name='property-chat'),
    path('<int:pk>/chat/sessions/', PropertyChatSessionListView.as_view(), name='property-chat-session-list-create'),
    path('<int:pk>/chat/sessions/<int:session_id>/', PropertyChatSessionDetailView.as_view(), name='property-chat-session-detail'),
]