from django.urls import path
from .views import (
    GenerateMemorandumView,
    MemorandumListView,
    MemorandumDetailView,
    MemorandumSectionUpdateView,
    SectionImageView,
)

app_name = 'memorandums'

urlpatterns = [
    # Generation
    path('generate/', GenerateMemorandumView.as_view(), name='memorandum-generate'),

    # Memorandum CRUD
    path('', MemorandumListView.as_view(), name='memorandum-list'),
    path('<int:pk>/', MemorandumDetailView.as_view(), name='memorandum-detail'),

    # Section endpoints
    path('<int:pk>/sections/<int:section_id>/', MemorandumSectionUpdateView.as_view(), name='memorandum-section-update'),
    path('<int:pk>/sections/<int:section_id>/image/', SectionImageView.as_view(), name='memorandum-section-image'),
]