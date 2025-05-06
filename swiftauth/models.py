import random
import uuid
import datetime
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
# -----------------------------------------------
#  CUSTOM USER MANAGER (Handles User Creation)
# -----------------------------------------------
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password."""
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)  # Ensure active by default
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with all permissions."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)  # Auto-verify superusers
        return self.create_user(email, password, **extra_fields)

# -----------------------------------------------
#  CUSTOM USER MODEL (Replaces Django’s Default)
# -----------------------------------------------
class User(AbstractUser):
    username = None  # Remove the default username field
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True)
    country = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)

    # National ID images for verification
    national_id_front = models.ImageField(upload_to="id_images/", blank=True, null=True)
    national_id_back = models.ImageField(upload_to="id_images/", blank=True, null=True)

    # Status fields
    is_active = models.BooleanField(default=True)  # Always active
    is_verified = models.BooleanField(default=False)  # Users need to verify email
    is_activated = models.BooleanField(default=False)  # Users must pay activation fee

    # OTP (One-Time Password) for authentication
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)

    # Password Reset models
    reset_token = models.CharField(max_length=100, blank=True, null=True)  
    reset_token_expiry = models.DateTimeField(null=True, blank=True)  

    objects = UserManager()  # Use custom manager

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone"]

    def __str__(self):
        return f"{self.email} - Verified: {self.is_verified} - Activated: {self.is_activated}"


    def generate_otp(self):
        """Generate a 6-digit OTP with a 10-minute expiry."""
        self.otp = str(random.randint(100000, 999999))
        self.otp_expiry = now() + datetime.timedelta(minutes=10)
        self.save()

    def generate_reset_token(self):
        """Generate a secure password reset token valid for 1 hour."""
        self.reset_token = str(uuid.uuid4())
        self.reset_token_expiry = now() + datetime.timedelta(hours=1)
        self.save()

# -----------------------------------------------
# ACCOUNT MODEL (Manages User Balances)

