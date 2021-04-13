from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from scram.users.api.views import UserViewSet
from scram.route_manager.api.views import ActionTypeViewSet, RouteViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("actiontypes", ActionTypeViewSet)
router.register("routes", RouteViewSet)


app_name = "api"
urlpatterns = router.urls
