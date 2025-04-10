from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from .forms import SignupForm, CustomAuthenticationForm, MandatoryPasswordChangeForm
from .models import Profile
import datetime
from django.contrib.auth.models import User

# Dictionnaire global pour bloquer temporairement les comptes (à améliorer avec cache ou base)
login_attempts = {}

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.create_user(username=form.cleaned_data['pseudonyme'], email=email, password=password)
            user.profile.pseudonyme = form.cleaned_data['pseudonyme']
            user.profile.avatar = form.cleaned_data['avatar']
            user.profile.must_change_password = True
            user.profile.save()
            login(request, user)
            return redirect('change_password')
    else:
        form = SignupForm()
    return render(request, 'users/signup.html', {'form': form})

def login_view(request):
    ip = request.META.get('REMOTE_ADDR')
    now = timezone.now()
    attempts = login_attempts.get(ip, {'count': 0, 'blocked_until': None})

    if attempts['blocked_until'] and now < attempts['blocked_until']:
        wait_time = int((attempts['blocked_until'] - now).total_seconds() // 1)
        return render(request, 'users/login_blocked.html', {'wait_time': wait_time})

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            login_attempts[ip] = {'count': 0, 'blocked_until': None}
            if request.user.profile.must_change_password:
                return redirect('change_password')
            return redirect('profile')
        else:
            attempts['count'] += 1
            if attempts['count'] >= 3:
                attempts['blocked_until'] = now + datetime.timedelta(minutes=2)
            login_attempts[ip] = attempts
            messages.error(request, "Nom d'utilisateur ou mot de passe invalide.")
    else:
        form = CustomAuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    return render(request, 'users/profile.html')

@login_required
def change_password_view(request):
    print("Début de la fonction change_password_view")
    if request.method == 'POST':
        print("Méthode POST détectée")
        form = MandatoryPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            print("Formulaire valide")
            user = form.save()
            update_session_auth_hash(request, user)
            profile = request.user.profile
            profile.must_change_password = False
            profile.save()
            messages.success(request, "Mot de passe changé avec succès.")
            return redirect('profile')
        else:
            print("Formulaire invalide :", form.errors)
    else:
        print("Méthode GET détectée")
        form = MandatoryPasswordChangeForm(user=request.user)
    return render(request, 'users/change_password.html', {'form': form})


def about_view(request):
    return render(request, 'users/about.html')