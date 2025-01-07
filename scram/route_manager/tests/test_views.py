"""Define simple tests for the template-based Views."""

from django.conf import settings
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


class HomePageLogoutTest(TestCase):
    """Verify that once logged out, we can't view anything."""

    def test_homepage_logout_links_missing(self):
        """After logout, we can't see anything."""
        response = self.client.get(reverse("route_manager:home"))
        response = self.client.post(reverse(settings.LOGOUT_URL), follow=True)
        self.assertEqual(reverse(settings.LOGOUT_URL), "blah")
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("route_manager:home"))

        self.assertNotContains(response, b"An admin user was created for you.")
        self.assertNotContains(response, b'type="submit">Logout')
        self.assertNotContains(response, b">Admin</a>")


class NotFoundTest(TestCase):
    """Verify that our custom 404 page is being served up."""

    def test_404(self):
        """Grab a bad URL."""
        response = self.client.get("/foobarbaz")
        self.assertContains(
            response, b'<div class="mb-4 lead">The page you are looking for was not found.</div>', status_code=404
        )
