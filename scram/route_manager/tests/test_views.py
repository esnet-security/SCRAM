"""Define simple tests for the template-based Views."""

from django.test import TestCase
from django.urls import resolve

from scram.route_manager.views import home_page


class HomePageTest(TestCase):
    """Test how the home page renders."""

    def test_root_url_resolves_to_home_page_view(self):
        """Ensure we can find the home page."""
        found = resolve("/")
        self.assertEqual(found.func, home_page)
