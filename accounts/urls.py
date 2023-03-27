from django.urls import include, path, reverse_lazy
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

from . import views
from .decorators import login_excluded, Swapt_admin_required

# Linking the views to URLs. Note that "auth_views" are generic views associated with accounts that Django implements. 
# This is where decorators are applied 
urlpatterns = [
    path('', views.index, name='index'),
    
    path('accounts/', include(([
        path('password-reset/', login_excluded('accounts:profile')(auth_views.PasswordResetView.as_view(template_name='accounts/password_reset_form.html', email_template_name='accounts/password_reset_email.html', success_url=reverse_lazy('accounts:password_reset_done'))), name='password_reset'),
        path('password-reset/done/', login_excluded('accounts:profile')(auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html')), name='password_reset_done'),
        path('password-reset/<uidb64>/<token>/', login_excluded('accounts:profile')(auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html', success_url=reverse_lazy('accounts:password_reset_complete'))), name='password_reset_confirm'),
        path('password-reset/complete/', login_excluded('accounts:profile')(auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_complete.html')), name='password_reset_complete'),
        path('password-change/',login_required()(auth_views.PasswordChangeView.as_view(template_name='accounts/password_change_form.html', success_url=reverse_lazy('accounts:password_change_done'))), name='password_change'),
        path('password-change/done/', login_required()(auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html')), name='password_change_done'),
        path('login/', login_excluded('accounts:profile')(auth_views.LoginView.as_view(template_name='accounts/signin.html')), name='login'),
        path('signup/', login_excluded('accounts:profile')(views.SignUpView.as_view()), name='signup'),
        path('signup/swapt-user/', login_excluded('accounts:profile')(views.SwaptUserSignUpView.as_view()), name='swaptuser_signup'),
        path('signup/property-manager/', login_excluded('accounts:profile')(views.propManager_SignUpView.as_view()), name='propertymanager_signup'),
        path('signup/swapt-admin', login_excluded('accounts:profile')(views.Swapt_AdminSignUpView.as_view()), name='Swapt_admin_signup'),
        path('profile/', login_required()(views.profile), name='profile'),
        path('profile/update/', login_required()(views.UserEditView.as_view()), name='edit_profile'),
        path('logout/', auth_views.LogoutView.as_view(template_name='accounts/logged_out.html'), name='logout'),
        path('activate/<uidb64>/<token>', views.Activate.as_view(), name='activate'),
        path('codes/create', Swapt_admin_required()(views.CodeCreationView.as_view()), name='code_creation'),
        path('codes/review', Swapt_admin_required()(views.CodeReviewView.as_view()), name='code_review')
    ], 'accounts'), namespace='accounts'))
    

]