# Standard library
from decimal import Decimal
import uuid
from datetime import timedelta


# Django core
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db import transaction as db_transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.timezone import now

# Local app
from .forms import RegisterForm, LoginForm
from .models import Account, User

# Auth user model
User = get_user_model()

def send_otp_email(user):
    subject = "SucuredSwiftPay Campany"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [user.email]

    html_content = render_to_string("emails/email.html", {"user": user})
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
    
def index(request):
    return render(request, 'index.html')


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            user.is_active = True  
            user.generate_otp()  # Generate OTP
            user.save()  # Ensure changes are saved
            Account.objects.create(user=user)  
            send_otp_email(user)
            request.session["verification_email"] = user.email  # Store email in session
            messages.success(request, "OTP sent to your email. Please verify your account.")
            return redirect("verify_email")
        else:
            messages.error(request, "Error in form submission. Please check the fields.")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})


def verify_email(request):
    email = request.session.get("verification_email")  # Retrieve email from session
    if not email:
        messages.error(request, "Invalid verification request.")
        return redirect("login")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, "User does not exist.")
        return redirect("login")

    if request.method == "POST":
        otp = request.POST.get("otp")

        if user.otp_expiry and user.otp_expiry < now():
            messages.error(request, "OTP expired. Click below to resend.")
            return render(request, "verify_email.html", {"email": email, "resend": True})

        if user.otp == otp:
            user.is_verified = True
            user.is_active = True  # ✅ Activate user after verification
            user.otp = None  # Clear OTP after verification
            user.save()
            messages.success(request, "Email verified! You can now log in.")
            return redirect("login")
        else:
            messages.error(request, "Invalid OTP.")

    return render(request, "verify_email.html", {"email": email})

def resend_otp(request):
    email = request.session.get("verification_email")
    if not email:
        messages.error(request, "Invalid request.")
        return redirect("login")

    try:
        user = User.objects.get(email=email)
        user.generate_otp()  # Generate new OTP
        send_otp_email(user)
        messages.success(request, "A new OTP has been sent to your email.")
    except User.DoesNotExist:
        messages.error(request, "User does not exist.")

    return redirect("verify_email")

def user_login(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            
            user = authenticate(request, username=email, password=password)
            
            if user is None:
                messages.error(request, "Invalid email or password.")
                return render(request, "login.html", {"form": form})
            
            if not user.is_verified:
                messages.error(request, "Your email is not verified. Please verify it to continue.")
                request.session["verification_email"] = user.email  # Store email in session
                user.generate_otp()  # Generate a new OTP
                send_otp_email(user)  # Send OTP via email
                return redirect("verify_email")  # Redirect to OTP verification page

            # ✅ Successful login
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("dashboard")
        
        else:
            messages.error(request, "Invalid email or password.")
    
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})

# Logout view
def user_logout(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")


def request_password_reset(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)

            # ✅ Only send reset link if user is verified
            if not user.is_verified:
                messages.error(request, "Your email is not verified. Please verify it first.")
                return redirect("password_reset")

            # Generate unique token
            token = str(uuid.uuid4())  # Random unique token
            user.reset_token = token
            user.reset_token_expiry = now() + timedelta(hours=1)  # Expire in 1 hour
            user.save()

            # Create reset URL
            reset_url = request.build_absolute_uri(reverse("reset_password", args=[token]))

            # Send reset email
            subject = "Reset Your Password - SwiftAuth"
            html_message = render_to_string("emails/password_reset_email.html", {"reset_url": reset_url})
            send_mail(subject, "", settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message)

            messages.success(request, "A password reset link has been sent to your email.")
            return redirect("login")

        except User.DoesNotExist:
            messages.error(request, "No account found with that email.")

    return render(request, "password_reset.html")


def reset_password(request, token):
    try:
        user = User.objects.get(reset_token=token)

        # Check if the token is expired
        if user.reset_token_expiry and user.reset_token_expiry < now():
            messages.error(request, "The reset link has expired. Please request a new one.")
            return redirect("password_reset")

    except User.DoesNotExist:
        messages.error(request, "Invalid reset token.")
        return redirect("password_reset")

    if request.method == "POST":
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "reset_password.html", {"token": token})

        # ✅ Strict password validation
        try:
            validate_password(new_password, user=user)  # Django built-in validation
        except ValidationError as e:
            messages.error(request, " ".join(e.messages))  # Show validation error
            return render(request, "reset_password.html", {"token": token})

        # ✅ If password is strong, update user password
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        user.save()

        messages.success(request, "Password successfully reset. You can now log in.")
        return redirect("login")

    return render(request, "reset_password.html", {"token": token})

@login_required
def dashboard(request):
    return render(request, "dashboard.html")

