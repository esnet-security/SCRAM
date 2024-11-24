"""Define simple tests for the template-based Views."""

from django.test import TestCase
from django.urls import resolve, reverse

from scram.route_manager.views import home_page


class HomePageTest(TestCase):
    """Test how the home page renders."""

    def test_root_url_resolves_to_home_page_view(self):
        """Ensure we can find the home page."""
        found = resolve("/")
        self.assertEqual(found.func, home_page)


class HomePageFirstVisitTest(TestCase):
    """Test how the home page renders the first time we view it."""

    def setUp(self):
        """Get the home page."""
        self.response = self.client.get(reverse("route_manager:home"))

    def test_first_homepage_view_has_userinfo(self):
        """The first time we view the home page, a user was created for us."""
        self.assertContains(self.response, b"An admin user was created for you.")

    def test_first_homepage_view_is_logged_in(self):
        """The first time we view the home page, we're logged in."""
        self.assertContains(self.response, b'type="submit">Logout')