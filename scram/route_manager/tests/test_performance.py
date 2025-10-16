"""Tests for performance (load time, DB queries, etc.)."""

import datetime
import time

from django.test import TestCase
from django.urls import reverse
from faker import Faker
from faker.providers import internet

from scram.route_manager.models import ActionType, Entry, Route


class TestViewNumQueries(TestCase):
    """Viewing an entry should only require one query."""

    NUM_ENTRIES = 100_000

    def setUp(self):
        """Set up the test environment."""
        self.fake = Faker()
        self.fake.add_provider(internet)

        # Query the homepage once to setup the user
        self.client.get(reverse("route_manager:home"))

        self.atype, _ = ActionType.objects.get_or_create(name="block")
        routes = [Route(route=self.fake.unique.ipv4_public()) for x in range(self.NUM_ENTRIES)]
        created_routes = Route.objects.bulk_create(routes)
        entries = [Entry(route=route, actiontype=self.atype, is_active=True) for route in created_routes]
        Entry.objects.bulk_create(entries)
        # Manually set the when time to be old so that we don't trigger `process_updates`
        # on all 100,000 of the test routes.
        Entry.objects.update(when=datetime.datetime(2000, 1, 1, 0, 0, tzinfo=datetime.UTC))

    def test_home_page(self):
        """Home page requires 11 queries.

        1. create transaction
        2. lookup session
        3. lookup user
        4. filter available actiontypes
        5. count entries with actiontype=1 and is_active
        6. count by user
        7. context processor active_count active blocks
        8. context processor active_count all blocks
        9. first page for actiontype=1
        10. close transaction
        """
        with self.assertNumQueries(10):
            start = time.time()
            self.client.get(reverse("route_manager:home"))
            time_taken = time.time() - start
            self.assertLess(time_taken, 1, "Home page took longer than 1 second")

    def test_entry_view(self):
        """Viewing an entry requires 8 queries.

        1. create transaction savepoint
        2. lookup session
        3. lookup user
        4. get entry
        5. rollback to savepoint
        6. release transaction savepoint
        7. context processor active_count active blocks
        8. context processor active_count all blocks
        """
        with self.assertNumQueries(8):
            start = time.time()
            self.client.get(reverse("route_manager:detail", kwargs={"pk": 9999}))
            time_taken = time.time() - start
            self.assertLess(time_taken, 1, "Entry detail page took longer than 1 second")

    def test_process_updates(self):
        """Process expired requires 6 queries.

        1. create transaction
        2. get entries_start active entry count
        3. find and delete expired entries
        4. get entries_end active entry count
        5. get new_entries from DB
        6. release transaction
        """
        with self.assertNumQueries(6):
            start = time.time()
            self.client.get(reverse("route_manager:process-updates"))
            time_taken = time.time() - start
            self.assertLess(time_taken, 1, "Process expired page took longer than 1 seconds")
