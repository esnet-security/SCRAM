from rest_framework.routers import DefaultRouter

from scram.route_manager.api.views import ActionTypeViewSet, EntryViewSet
from scram.users.api.views import UserViewSet

router = DefaultRouter()

router.register("users", UserViewSet)
router.register("actiontypes", ActionTypeViewSet)
router.register("entrys", EntryViewSet)


app_name = "api"
urlpatterns = router.urls
