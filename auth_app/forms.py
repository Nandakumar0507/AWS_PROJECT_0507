from django import forms
from django.contrib.auth import get_user_model

from .models import Role

User = get_user_model()


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    class Meta:
        model = User
        fields = ["display_name", "email", "username", "password", "confirm_password"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["display_name", "email"]


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)

    class Meta:
        model = User
        fields = ["email", "username", "display_name", "role", "password"]

    def clean_role(self):
        role = self.cleaned_data["role"]
        if role not in {Role.PATIENT, Role.CLINICIAN}:
            raise forms.ValidationError("Only patient and clinician accounts are created from this screen.")
        return role
