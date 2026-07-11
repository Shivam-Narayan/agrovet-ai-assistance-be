from rest_framework import serializers
from .models import User, UserActivity
from django.contrib.auth import authenticate
import json
import os
import logging

logger = logging.getLogger(__name__)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
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

# serializer.py

class UserActivitySerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
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
        fields = ['email', 'name', 'is_admin', 'activities']

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()