from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, inline_serializer, OpenApiTypes
from rest_framework import serializers
import logging
from django.utils.dateparse import parse_date
from rest_framework.pagination import PageNumberPagination
from collections import defaultdict
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from .serializers import (
    RegisterSerializer, LoginSerializer, ErrorResponseSerializer, UserActivitySerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer, LogoutSerializer, UserDetailSerializer
)
from .models import UserActivity

logger = logging.getLogger(__name__)
User = get_user_model()

class RegisterAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @extend_schema(
        tags=['Account'],
        summary="Register a new user",
        description="Register a new user and send a verification email.",
        responses={
            201: inline_serializer(
                name='RegisterResponse',
                fields={
                    'message': serializers.CharField(),
                }
            ),
            400: ErrorResponseSerializer
        }
    )
    def post(self, request, *args, **kwargs):
        """Register a new user and send a verification email."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Send Email Verification
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verify_url = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"
            
            send_mail(
                'Verify your email for Agrovet',
                f'Please click the following link to verify your email:\n{verify_url}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            # Log registration activity
            UserActivity.objects.create(
                user=user,
                activity_type='registration',
                details={'message': 'User registered'}
            )
            return Response({
                "message": "User registered successfully. Please check your email to verify your account.",
            }, status=status.HTTP_201_CREATED)
            
        return Response(
            ErrorResponseSerializer({'error': serializer.errors}).data,
            status=status.HTTP_400_BAD_REQUEST
        )


class VerifyEmailAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Account'],
        summary="Verify Email Address",
        description="Verify user's email using the token sent to their inbox.",
        responses={
            200: inline_serializer(
                name='VerifyEmailResponse',
                fields={'message': serializers.CharField()}
            ),
            400: inline_serializer(
                name='VerifyEmailError',
                fields={'error': serializers.CharField()}
            )
        }
    )
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_email_verified = True
            user.save()
            return Response({"message": "Email verified successfully."}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Account'],
        summary="Login User",
        description="Authenticate a user or admin and return a JWT access and refresh token.",
        request=LoginSerializer,
        responses={
            200: inline_serializer(
                name='LoginResponse',
                fields={
                    'message': serializers.CharField(),
                    'access': serializers.CharField(),
                    'refresh': serializers.CharField(),
                    'user': inline_serializer(
                        name='LoginUserDetail',
                        fields={
                            'email': serializers.EmailField(),
                            'name': serializers.CharField(),
                            'is_admin': serializers.BooleanField(),
                        }
                    )
                }
            ),
            400: ErrorResponseSerializer
        }
    )
    def post(self, request, *args, **kwargs):
        """Authenticate a user or admin and return a JWT access and refresh token."""
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                ErrorResponseSerializer({'error': serializer.errors}).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = serializer.validated_data.get("user")
        is_admin = serializer.validated_data.get("is_admin", False)
        
        refresh = RefreshToken.for_user(user)
        
        # Log login activity
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            details={'message': 'User logged in', 'is_admin': is_admin}
        )
        return Response({
            "message": "Login successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "email": user.email,
                "name": user.name,
                "is_admin": user.is_admin
            }
        }, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Account'],
        summary="Logout User",
        description="Blacklist the given refresh token.",
        request=LogoutSerializer,
        responses={
            204: None,
            400: ErrorResponseSerializer
        }
    )
    def post(self, request, *args, **kwargs):
        """Blacklist the refresh token to logout."""
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Successfully logged out."}, status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Account'],
        summary="Request Password Reset",
        description="Sends a password reset link to the given email if the user exists.",
        request=PasswordResetRequestSerializer,
        responses={
            200: inline_serializer(
                name='PasswordResetRequestResponse',
                fields={'message': serializers.CharField()}
            ),
            400: ErrorResponseSerializer
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.filter(email=email).first()
            if user:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
                
                send_mail(
                    'Password Reset Request',
                    f'Click the following link to reset your password:\n{reset_url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            return Response({"message": "If an account with this email exists, a reset link has been sent."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Account'],
        summary="Confirm Password Reset",
        description="Verify token and update the user's password.",
        request=PasswordResetConfirmSerializer,
        responses={
            200: inline_serializer(
                name='PasswordResetConfirmResponse',
                fields={'message': serializers.CharField()}
            ),
            400: inline_serializer(
                name='PasswordResetConfirmError',
                fields={'error': serializers.CharField()}
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            uidb64 = serializer.validated_data['uidb64']
            token = serializer.validated_data['token']
            password = serializer.validated_data['password']

            try:
                uid = force_str(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None

            if user is not None and default_token_generator.check_token(user, token):
                user.set_password(password)
                user.save()
                return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivityLogAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Account'],
        summary="Retrieve Activity Logs",
        description="Retrieve login and prediction activities. Admin users can view activities of all users, while regular users can view only their own activities.",
        parameters=[
            OpenApiParameter('user_id', type=int, description='Optional: Filter activities by specific user ID (admin only)'),
            OpenApiParameter('start_date', type=OpenApiTypes.DATE, description='Optional: Filter activities from this start date (format: YYYY-MM-DD)'),
            OpenApiParameter('end_date', type=OpenApiTypes.DATE, description='Optional: Filter activities up to this end date (format: YYYY-MM-DD)'),
            OpenApiParameter('group_by_day', type=bool, description="Optional: Set to 'true' to group activities by day (default is false)"),
        ],
        responses={
            200: inline_serializer(
                name='ActivityLogResponse',
                fields={
                    'count': serializers.IntegerField(),
                    'next': serializers.CharField(allow_null=True),
                    'previous': serializers.CharField(allow_null=True),
                    'results': UserActivitySerializer(many=True)
                }
            ),
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer
        }
    )
    def get(self, request, *args, **kwargs):
        """Retrieve login and prediction activities."""
        user = request.user
        user_id = request.query_params.get('user_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        group_by_day = request.query_params.get('group_by_day', 'false').lower() == 'true'

        if user.is_admin:
            activities = UserActivity.objects.filter(activity_type__in=['login', 'prediction'])
            if user_id:
                activities = activities.filter(user_id=user_id)
        else:
            activities = UserActivity.objects.filter(user=user, activity_type__in=['login', 'prediction'])

        if start_date:
            start_date_obj = parse_date(start_date)
            if start_date_obj:
                activities = activities.filter(timestamp__date__gte=start_date_obj)
        if end_date:
            end_date_obj = parse_date(end_date)
            if end_date_obj:
                activities = activities.filter(timestamp__date__lte=end_date_obj)

        activities = activities.order_by('-timestamp')

        if group_by_day:
            grouped = defaultdict(list)
            for activity in activities:
                day_str = activity.timestamp.date().isoformat()
                grouped[day_str].append(UserActivitySerializer(activity).data)

            result = [{'date': date, 'activities': acts} for date, acts in sorted(grouped.items(), reverse=True)]
            return Response(result, status=status.HTTP_200_OK)

        # Manual Pagination Setup
        paginator = PageNumberPagination()
        paginator.page_size = 10
        paginated_qs = paginator.paginate_queryset(activities, request)

        serialized = UserActivitySerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serialized.data)
