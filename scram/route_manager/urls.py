from django.urls import path

from .api import views

app_name = 'route_manager'

urlpatterns = [
    path(route='api/', view=views.RouteView.as_view(), name='api_root'),
    path(route='api/<path:route>/',
         view=views.RouteDetailView.as_view(),
         name='api_route_detail')
]
