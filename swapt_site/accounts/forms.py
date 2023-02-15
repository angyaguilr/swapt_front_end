from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.db import transaction
from django.forms import ModelForm

from .validators import validate_email, validate_code
from .models import Swapt_admin, SwaptUser, User, Code, propManager


class SwaptUserSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ( "first_name", "last_name", "campusSignUp", "username", "email", "password1", "password2" )

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_swapt_user = True
        user.is_active = False
        user.save()
        swaptuser = SwaptUser.objects.create(user=user)
        return user

class Swapt_AdminSignUpForm(UserCreationForm):
    # Using validate_email validator to ensure a user can only sign up as an Swapt admin with an Swapt admin email address
    email = forms.EmailField(validators=[validate_email])

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_admin = True
        if commit:
            user.is_active = False
            user.save()
            admin = Swapt_admin.objects.create(user=user)
        return user

class propManager_SignUpForm(UserCreationForm):
     # Using validate_code validator to ensure swaptusers can only sign up with a valid sign up code
    code = forms.CharField(min_length=6, max_length=50, validators=[validate_code])
    # "locationSignUp", "propNameSignUp"
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2", "code",)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_admin = True
        if commit:
            user.is_active = False
            user.save()
            propmanager = propManager.objects.create(user=user)
        return user        

class UserEditForm(UserChangeForm):

    class Meta(UserChangeForm.Meta):
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

class CodeCreationForm(ModelForm):

    code = forms.CharField(min_length=6, max_length=50)
    
    class Meta(UserChangeForm.Meta):
        model = Code
        fields = ("code", )