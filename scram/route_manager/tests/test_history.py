from django.test import TestCase
from simple_history.utils import get_change_reason_from_object, update_change_reason

from scram.route_manager.models import ActionType, Entry, Route


class TestActiontypeHistory(TestCase):
    def setUp(self):
        self.atype = ActionType.objects.create(name="Block")

    def test_comments(self):
        self.atype.name = "Nullroute"
        self.atype._change_reason = "Use more descriptive name"
        self.atype.save()
        self.assertIsNotNone(get_change_reason_from_object(self.atype))


class TestEntryHistory(TestCase):
    routes = ["192.0.2.16/32", "198.51.100.16/28"]

    def setUp(self):
        self.atype = ActionType.objects.create(name="Block")
        for r in self.routes:
            route = Route.objects.create(route=r)
            entry = Entry.objects.create(route=route, actiontype=self.atype)
            create_reason = "Zeek detected a scan from 192.0.2.1."
            update_change_reason(entry, create_reason)
            self.assertEqual(entry.get_change_reason(), create_reason)

    def test_comments(self):
        for r in self.routes:
            route_old = Route.objects.get(route=r)
            e = Entry.objects.get(route=route_old)
            self.assertEqual(e.get_change_reason(), "Zeek detected a scan from 192.0.2.1.")

            route_new = str(route_old).replace("16", "32")
            e.route = Route.objects.create(route=route_new)

            change_reason = "I meant 32, not 16."
            e._change_reason = change_reason
            e.save()

            self.assertEqual(len(e.history.all()), 2)
            self.assertEqual(e.get_change_reason(), change_reason)
