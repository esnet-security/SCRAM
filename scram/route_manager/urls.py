from django.urls import path

from . import views

app_name = "route_manager"

urlpatterns = [
    path("", views.home_page, name="home"),
    path("/search/", views.search_entries, name="search"),
]
