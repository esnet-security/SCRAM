from django.urls import path

from . import views

app_name = "route_manager"

urlpatterns = [
    path("", views.home_page, name="home"),
    path("search/", views.search_entries, name="search"),
    path("delete/<int:pk>/", views.delete_entry, name="delete"),
    path(route="<int:pk>/", view=views.EntryDetailView.as_view(), name="detail"),
    path("entries/", views.EntryListView.as_view(), name="entry-list"),
    path("add/", views.add_entry, name="add"),
    path("status/<int:pk>/", views.status_entry, name="status"),
]
