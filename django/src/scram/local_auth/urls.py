"""Register URLs for local auth known to Django, and the View that will handle each."""

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

app_name = "local_auth"

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="local_auth/login.html", success_url="route_manager:home"
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
]
