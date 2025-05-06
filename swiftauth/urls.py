from django.urls import path,include
from . import views
from . import apiviews
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [

    # Views
    path("", views.index, name="index"),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Fix: Remove email parameter from verify_email
    path('verify-email/', views.verify_email, name='verify_email'),  
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path("password-reset/", views.request_password_reset, name="password_reset"),
    path("password-reset/<str:token>/", views.reset_password, name="reset_password"),
    # path("api/deposit/", views.deposit, name="deposit"),
    
 ]
