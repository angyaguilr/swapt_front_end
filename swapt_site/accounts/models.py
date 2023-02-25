from django.db import models
from django.contrib.auth.models import AbstractUser

# User model for website
class User(AbstractUser):
    email = models.EmailField(max_length=254, unique=True)
    is_swapt_user = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_PM_admin = models.BooleanField(default=False)
   
    CAMPUS_CHOICES = [
        ('Elon University', 'Elon University'),
        ('University of Maryland', 'University of Maryland'),
    ]
    campusSignUp = models.CharField(
        max_length=50,
        choices=CAMPUS_CHOICES,
        null=True
        )

# SwaptUser model that's attached to user model
class SwaptUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

# Learn Fresh admin model that's attached to user model
class Swapt_admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

class propManager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)    

# Code model for sign up codes
class Code(models.Model):
    code = models.CharField(max_length=50, primary_key=True, unique=True)
    PROPNAME_CHOICES = [
        ('PropertyName1', 'PropertyName1'),
        ('PropertyName2', 'PropertyName2'),
    ]
    campusSignUp = models.CharField(
        max_length=50,
        choices= PROPNAME_CHOICES,
        null=True
        )
