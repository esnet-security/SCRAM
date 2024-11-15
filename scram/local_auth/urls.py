from django.contrib.auth import views as auth_views
from django.urls import path

app_name = "local_auth"

urlpatterns = [
    path("login/", auth_views.login, {"template_name": "account/login.html"}, name="login"),
    path("logout/", auth_views.logout, {"template_name": "logged_out.html"}, name="logout"),
]
