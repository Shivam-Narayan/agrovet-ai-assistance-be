from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=False)  # Explicit flag for business logic
    
    objects = CustomUserManager()

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='agrovet_user_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='agrovet_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    USERNAME_FIELD = 'email'
    # username is auto-generated in the manager, so it doesn't need to be prompted in createsuperuser
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

    def delete(self, *args, **kwargs):
        """Soft delete: instead of removing from DB, deactivate the user."""
        self.is_active = False
        self.save()

class UserActivity(models.Model):
    class ActivityType(models.TextChoices):
        LOGIN = 'login', 'Login'
        REGISTRATION = 'registration', 'Registration'
        PREDICTION = 'prediction', 'Prediction'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(
        max_length=50, 
        choices=ActivityType.choices,
        default=ActivityType.LOGIN
    )
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()} at {self.timestamp}"