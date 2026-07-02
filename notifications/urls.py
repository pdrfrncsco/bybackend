from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationsListView.as_view(), name='notifications-list'),
    path('unread-count/', views.UnreadCountView.as_view(), name='notifications-unread-count'),
    path('<int:pk>/mark-read/', views.MarkReadView.as_view(), name='notifications-mark-read'),
]
