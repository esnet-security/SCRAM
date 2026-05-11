"""Map the API routes to the views."""

from rest_framework.routers import DefaultRouter

from scram.route_manager.api.views import (
    ActionTypeViewSet,
    ClientViewSet,
    EntryViewSet,
    IgnoreEntryViewSet,
    IsActiveViewSet,
)
from scram.users.api.views import UserViewSet

router = DefaultRouter()

# The basename parameter is really only required for the IsActiveViewSet since that has a dynamic queryset.
# The others have a static queryset so they don't strictly require it. I added it for consistency.
router.register("users", UserViewSet, basename="user")
router.register("actiontypes", ActionTypeViewSet, basename="actiontype")
router.register("register_client", ClientViewSet, basename="client")
router.register("entries", EntryViewSet, basename="entry")
router.register("ignore_entries", IgnoreEntryViewSet, basename="ignoreentry")
router.register("is_active", IsActiveViewSet, basename="is_active")

app_name = "api"
urlpatterns = router.urls
