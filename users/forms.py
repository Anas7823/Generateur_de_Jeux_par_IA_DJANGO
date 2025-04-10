from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.forms import PasswordChangeForm

class SignupForm(forms.ModelForm):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    avatar = forms.ImageField()

    class Meta:
        model = Profile
        fields = ['pseudonyme', 'avatar']

    def clean_pseudonyme(self):
        pseudonyme = self.cleaned_data['pseudonyme']
        if any(char.isdigit() for char in pseudonyme):
            raise forms.ValidationError("Le pseudonyme ne doit pas contenir de chiffres.")
        if len(pseudonyme) < 5:
            raise forms.ValidationError("Le pseudonyme doit contenir au moins 5 caractères.")
        return pseudonyme

class CustomAuthenticationForm(AuthenticationForm):
    # Nous pourrons y injecter une logique si besoin (ex: vérif de blocage)
    pass

class MandatoryPasswordChangeForm(PasswordChangeForm):
    pass
