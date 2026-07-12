from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterAPIView, LoginAPIView, ActivityLogAPIView,
    LogoutAPIView, VerifyEmailAPIView, PasswordResetRequestAPIView, PasswordResetConfirmAPIView
)

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('verify-email/<str:uidb64>/<str:token>/', VerifyEmailAPIView.as_view(), name='verify_email'),
    path('password-reset/', PasswordResetRequestAPIView.as_view(), name='password_reset'),
    path('password-reset-confirm/', PasswordResetConfirmAPIView.as_view(), name='password_reset_confirm'),
    
    path('activity-log/', ActivityLogAPIView.as_view(), name='activity_log'),
]