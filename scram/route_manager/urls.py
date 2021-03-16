from django.urls import path

from .api import views

app_name = 'route_manager'

urlpatterns = [
    path(route='api/', view=views.IPAddressListCreateAPIView.as_view(), name='ipaddress_rest_api'),
    path(route='api/<uuid:uuid>/',
         view=views.IPAddressRetrieveUpdateDestroyAPIView.as_view(),
         name='ipaddress_rest_api')
]
