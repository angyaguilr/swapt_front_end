from django.contrib import admin
from .models import User, SwaptUser, Swapt_admin, Code, propManager

# Registering the models in this app so the admin can view and edit these types of objects
admin.site.register(User)
admin.site.register(SwaptUser)
admin.site.register(Swapt_admin)
admin.site.register(propManager)
admin.site.register(Code)
