from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect


def swapt_user_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='accounts:login'):
    '''
    Decorator for views that checks that the logged in user is a swaptuser,
    redirects to the log-in page if the user is not a swaptuser. For example,
    this is used to ensure swaptusers can't access the create sign up code page.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_swapt_user,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def Swapt_admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='accounts:login'):
    '''
    Decorator for views that checks that the logged in user is an Swapt admin,
    redirects to the log-in page if the user is not an Swapt admin. For example,
    this is used to ensure Swapt admin can't access the upload listing page.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_admin,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator   

def login_excluded(redirect_to):
    """ 
    This decorator redirectes logged-in users to the provided "redirect_to" URL.
    For example, this is used to ensure logged-in users can't access the login 
    or signup pages.
    """ 
    def _method_wrapper(view_method):
        def _arguments_wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                return redirect(redirect_to) 
            return view_method(request, *args, **kwargs)
        return _arguments_wrapper
    return _method_wrapper