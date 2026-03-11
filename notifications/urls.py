from django.urls import path
from .views import (
    NotificationListView,
    UnreadCountView,
    MarkAsReadView,
    MarkAllAsReadView,
    DeleteNotificationView,
    ClearAllNotificationsView,
)

app_name = 'notifications'

urlpatterns = [
    # List all notifications for the authenticated user
    path('', NotificationListView.as_view(), name='notification-list'),

    # Unread badge count — used by the frontend notification bell
    path('unread-count/', UnreadCountView.as_view(), name='unread-count'),

    # Bulk operations — must come before {id}/ to avoid URL conflicts
    path('read-all/',   MarkAllAsReadView.as_view(),        name='mark-all-read'),
    path('clear-all/',  ClearAllNotificationsView.as_view(), name='clear-all'),

    # Single notification operations
    path('<int:pk>/read/', MarkAsReadView.as_view(),        name='mark-read'),
    path('<int:pk>/',      DeleteNotificationView.as_view(), name='delete'),
]