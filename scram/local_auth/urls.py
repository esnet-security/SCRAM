from django.urls import path

from scram.local_auth.views import login, logout

app_name = "users"
urlpatterns = [
    path("login/", view=login, name="update"),
    path("logout/", view=logout, name="detail"),
]
