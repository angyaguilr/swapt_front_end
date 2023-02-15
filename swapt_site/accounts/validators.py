from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Code

# Validates email by checking if the email ends with "learnfresh.org"
# If it doesn't, throws an error
def validate_email(value):
    if not value.endswith("swapt.it"):
        raise ValidationError(
            _('%(value)s is not a Swapt email'),
            params={'value': value},
        )

# Validates code by trying to get a code object with given string
# If no such code exists, throws an error
def validate_code(value):
    try:
        Code.objects.get(code=value)
    
    except(Code.DoesNotExist):
        raise ValidationError(
            _('%(value)s is not a valid code'),
            params={'value': value},
        )