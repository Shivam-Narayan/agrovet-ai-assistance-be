from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from drf_yasg.utils import swagger_auto_schema
import logging
from django.utils.dateparse import parse_date
from rest_framework.pagination import PageNumberPagination
from collections import defaultdict

from .serializers import RegisterSerializer, LoginSerializer, ErrorResponseSerializer, UserActivitySerializer
from .models import UserActivity
from .swagger import REGISTER_SWAGGER, LOGIN_SWAGGER, Activity_Log_SWAGGER

logger = logging.getLogger(__name__)

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(**REGISTER_SWAGGER)
    def post(self, request, *args, **kwargs):
        """Register a new user and return a JWT access token."""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Log registration activity
            UserActivity.objects.create(
                user=user,
                activity_type='registration',
                details={'message': 'User registered'}
            )
            return Response({
                "message": "User registered successfully",
            }, status=status.HTTP_201_CREATED)
        return Response(
            ErrorResponseSerializer({'error': serializer.errors}).data,
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(**LOGIN_SWAGGER)
    def post(self, request, *args, **kwargs):
        """Authenticate a user or admin and return a JWT access token."""
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                ErrorResponseSerializer({'error': serializer.errors}).data,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = serializer.validated_data.get("user")
        is_admin = serializer.validated_data.get("is_admin", False)
        
        if not user:
            return Response(
                ErrorResponseSerializer({'error': 'Invalid credentials'}).data,
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        access_token = AccessToken.for_user(user)
        
        # Log login activity
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            details={'message': 'User logged in', 'is_admin': is_admin}
        )
        return Response({
            "message": "Login successful",
            "token": str(access_token),
        }, status=status.HTTP_200_OK)


class ActivityLogAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(**Activity_Log_SWAGGER)
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
