"""Define forms for the Admin site."""

from django.contrib.auth import forms as admin_forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserChangeForm(admin_forms.UserChangeForm):
    """Define a form to edit a User."""

    class Meta(admin_forms.UserChangeForm.Meta):
        """Map to the User model."""

        model = User


class UserCreationForm(admin_forms.UserCreationForm):
    """Define a form to create a User."""

    class Meta(admin_forms.UserCreationForm.Meta):
        """Map to the User model and provide custom error messages."""

        model = User

        error_messages = {
            "username": {"unique": _("This username has already been taken.")}
        }
