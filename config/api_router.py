"""Map the API routes to the views."""

from rest_framework.routers import DefaultRouter

from scram.route_manager.api.views import ActionTypeViewSet, ClientViewSet, EntryViewSet, IgnoreEntryViewSet
from scram.users.api.views import UserViewSet

router = DefaultRouter()

router.register("users", UserViewSet)
router.register("actiontypes", ActionTypeViewSet)
router.register("register_client", ClientViewSet)
router.register("entries", EntryViewSet)
router.register("ignore_entries", IgnoreEntryViewSet)
router.register("is_blocked", IsBlockedViewSet, "is_blocked")

app_name = "api"
urlpatterns = router.urls
