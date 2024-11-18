"""Define tests for the Views of the Users application."""

import pytest
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.urls import reverse

from scram.users.forms import UserChangeForm
from scram.users.models import User
from scram.users.tests.factories import UserFactory
from scram.users.views import UserRedirectView, UserUpdateView, user_detail_view

pytestmark = pytest.mark.django_db


class TestUserUpdateView:
    """
    Define tests related to the Update View.

    TODO:
        extracting view initialization code as class-scoped fixture
        would be great if only pytest-django supported non-function-scoped
        fixture db access -- this is a work-in-progress for now:
        https://github.com/pytest-dev/pytest-django/pull/258
    """

    def test_get_success_url(self, user: User, rf: RequestFactory):
        """Ensure we can view an arbitrary URL."""
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert view.get_success_url() == f"/users/{user.username}/"

    def test_get_object(self, user: User, rf: RequestFactory):
        """Ensure we can retrieve the User object."""
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert view.get_object() == user

    def test_form_valid(self, user: User, rf: RequestFactory):
        """Ensure the form validation works."""
        view = UserUpdateView()
        request = rf.get("/fake-url/")

        # Add the session/message middleware to the request
        SessionMiddleware(get_response=request).process_request(request)
        MessageMiddleware(get_response=request).process_request(request)
        request.user = user

        view.request = request

        # Initialize the form
        form = UserChangeForm()
        form.cleaned_data = []
        view.form_valid(form)

        messages_sent = [m.message for m in messages.get_messages(request)]
        assert messages_sent == ["Information successfully updated"]


class TestUserRedirectView:
    """Define tests related to the Redirect View."""

    def test_get_redirect_url(self, user: User, rf: RequestFactory):
        """Ensure the redirection URL works."""
        view = UserRedirectView()
        request = rf.get("/fake-url")
        request.user = user

        view.request = request

        assert view.get_redirect_url() == f"/users/{user.username}/"


class TestUserDetailView:
    """Define tests related to the User Detail View."""

    def test_authenticated(self, user: User, rf: RequestFactory):
        """Ensure an authenticated user has access."""
        request = rf.get("/fake-url/")
        request.user = UserFactory()

        response = user_detail_view(request, username=user.username)

        assert response.status_code == 200

    def test_not_authenticated(self, user: User, rf: RequestFactory):
        """Ensure an unauthenticated user gets redirected to login."""
        request = rf.get("/fake-url/")
        request.user = AnonymousUser()

        response = user_detail_view(request, username=user.username)
        login_url = reverse(settings.LOGIN_URL)

        assert response.status_code == 302
        assert response.url == f"{login_url}?next=/fake-url/"
