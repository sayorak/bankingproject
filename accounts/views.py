from django.shortcuts import render, redirect
from django.contrib.auth import login, logout

from bankapp.models import Notification
from .forms import CustomUserCreationForm, CustomAuthenticationForm

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            Notification.objects.create(user=user, message='Аккаунт успешно зарегистрирован')
            return redirect('wallets')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/registration.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            Notification.objects.create(user=user, message='Пользователь вошел в систему')
            return redirect('wallets')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('wallets')
