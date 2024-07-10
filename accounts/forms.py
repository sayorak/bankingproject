from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from accounts.models import Profile


class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(max_length=100, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'full_name']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.save()

        full_name = self.cleaned_data['full_name']
        profile, created = Profile.objects.get_or_create(user=user, defaults={'full_name': full_name})

        if not created:
            profile.full_name = full_name
            profile.save()

        return user

class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ['username', 'password']

        

