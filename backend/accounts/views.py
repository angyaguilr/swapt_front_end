from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.urls import reverse_lazy

from django.core.mail import EmailMessage
from django.views.generic import CreateView, TemplateView, View, UpdateView
from django.views.generic.edit import UpdateView

from .forms import SwaptUserSignUpForm, Swapt_AdminSignUpForm, UserEditForm, CodeCreationForm, propManager_SignUpForm
from .models import User, Code
from .tokens import account_activation_token

from django.http import HttpResponse


# Landing page view
def index(request):
    return render(request, 'lander.html', {"user": request.user})

# Profile page view
def profile(request):
    return render(request, 'accounts/profile.html', {"user": request.user})

# Confirmation email creation/sending logic
def sendEmail(user, form, request):
    mail_subject = 'Activate your account.'
    current_site = get_current_site(request)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    activation_link = "{0}/accounts/activate/{1}/{2}".format(current_site, uid, token)
    message = "Hello {0},\n {1}".format(user.username, activation_link)
    to_email = form.cleaned_data.get('email')
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.send()
    return HttpResponse('Please confirm your email address to complete the registration')

# Signup page where the user chooses whether to sign up as a swaptuser or Swapt Admin
class SignUpView(TemplateView):
    template_name = 'accounts/signup.html'

# Profile edit page
class UserEditView(UpdateView):
    form_class = UserEditForm
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

# SwaptUser signup page (don't need Swapt email address, do need sign up code)
class SwaptUserSignUpView(CreateView):
    model = User
    # The sign up code requirement comes from this form
    form_class = SwaptUserSignUpForm
    template_name = 'accounts/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'swaptuser'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        return sendEmail(user, form, self.request)

class propManager_SignUpView(CreateView):
    model = User
    # The sign up code requirement comes from this form
    form_class = propManager_SignUpForm
    template_name = 'accounts/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'propManager'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        return sendEmail(user, form, self.request)  

# Swapt Admin signup page (do need Swapt email address, don't sign up code)
class Swapt_AdminSignUpView(CreateView):
    model = User
    # The Swapt admin email requirement comes from this form
    form_class = Swapt_AdminSignUpForm
    template_name = 'accounts/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'Swapt_admin'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        return sendEmail(user, form, self.request)

# Uses activation link sent in email to activate the user if the link is valid
class Activate(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        # Catches if the activation link is bad
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and account_activation_token.check_token(user, token):
            # Sets the user to active
            user.is_active = True
            user.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return redirect("index")
        else:
            return HttpResponse("Error, invalid link.")

# View for code creation
class CodeCreationView(CreateView):
    model = Code
    form_class = CodeCreationForm
    template_name = 'accounts/code_create_form.html'

    def form_valid(self, form):
        code = form.save()
        return HttpResponse("Successful code creation.")

# Simple view for reviewing sign up codes. Allows Swapt admin to view and delete existing codes
class CodeReviewView(View):

    def get(self, request):
        template = "accounts/review_codes.html"
        context = {"codes": Code.objects.all()}
        return render(request, template, context)
    
    def post(self, request):
        code = Code.objects.get(code=request.POST['id'])
        if request.POST.get('status'):
            try:
                code.delete()
            except(TypeError, ValueError, OverflowError):
                return HttpResponse("Failed to delete code")
        
        return redirect("accounts:code_review")