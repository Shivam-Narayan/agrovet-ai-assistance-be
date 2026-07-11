from django.urls import path
from .views import RegisterAPIView, LoginAPIView, ActivityLogAPIView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('activity-log/', ActivityLogAPIView.as_view(), name='activity_log'),
]