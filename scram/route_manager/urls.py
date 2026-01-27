"""Register URLs known to Django, and the View that will handle each."""

from django.urls import path

from . import views

app_name = "route_manager"

urlpatterns = [
    path("", views.home_page, name="home"),
    path("search/", views.search_entries, name="search"),
    path("process_updates/", views.process_updates, name="process-updates"),
    path("delete/<int:pk>/", views.delete_entry, name="delete"),
    path(route="<int:pk>/", view=views.EntryDetailView.as_view(), name="detail"),
    path("entries/", views.EntryListView.as_view(), name="entry-list"),
    path("add/", views.add_entry, name="add"),
    path("health/", views.health, name="health"),
]
