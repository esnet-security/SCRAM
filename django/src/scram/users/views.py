"""Define the Views that will handle the HTTP requests."""

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, RedirectView, UpdateView

User = get_user_model()


class UserDetailView(LoginRequiredMixin, DetailView):
    """Map this view to the User model, and rely on the DetailView generic view."""

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Map this view to the User model, and rely on the UpdateView generic view."""

    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self):
        """Return the User detail view."""
        return reverse("users:detail", kwargs={"username": self.request.user.username})

    def get_object(self):
        """Return the User object."""
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    """Map this view to the User model, and rely on the RedirectView generic view."""

    permanent = False

    def get_redirect_url(self):
        """Return the User detail view."""
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()
