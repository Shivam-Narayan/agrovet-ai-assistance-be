from rest_framework import serializers
from .models import UserActivity
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
import json
import os
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['email', 'name', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords must match"})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password'],
            username=validated_data['email']
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")
        logger.debug(f"Attempting login for email: {email}")

        # Use standard Django authentication
        user = authenticate(username=email, password=password)
        if not user:
            logger.error(f"Authentication failed for {email}")
            raise serializers.ValidationError("Invalid credentials")

        logger.info(f"User authenticated: {email}, is_admin: {getattr(user, 'is_admin', False)}")
        data["user"] = user
        data["is_admin"] = getattr(user, 'is_admin', False)
        return data


class UserActivitySerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    name = serializers.CharField(source='user.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    is_admin = serializers.BooleanField(source='user.is_admin', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        model = UserActivity
        fields = ['activity_type', 'details', 'timestamp', 'user_id', 'username', 'is_admin', 'email', 'name']


class UserDetailSerializer(serializers.ModelSerializer):
    activities = UserActivitySerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ['email', 'name', 'is_admin', 'is_email_verified', 'activities']

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    token = serializers.CharField(required=True)
    uidb64 = serializers.CharField(required=True)

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            self.fail('bad_token')