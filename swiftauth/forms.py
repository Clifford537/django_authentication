from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    phone = forms.CharField(max_length=15)
    country = forms.CharField(max_length=100)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    national_id_front = forms.ImageField(required=True)
    national_id_back = forms.ImageField(required=True)

    class Meta:
        model = User
        fields = ['email', 'phone', 'first_name', 'last_name', 'country', 
                  'date_of_birth', 'national_id_front', 'national_id_back', 
                  'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False  # Don't activate user until verified
        user.generate_otp()  # Generate OTP and expiry time
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")  # Override username field to use email
from django import forms

