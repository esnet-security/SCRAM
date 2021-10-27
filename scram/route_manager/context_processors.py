from django.conf import settings
from django.urls import reverse


def login_logout(request):
    login_url = reverse(settings.LOGIN_URL)
    logout_url = reverse(settings.LOGOUT_URL)
    return {"login": login_url, "logout": logout_url}
