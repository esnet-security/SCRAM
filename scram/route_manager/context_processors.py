from django.conf import settings


def login_logout(request):
    return {"login": settings.LOGIN_URL, "logout": settings.LOGOUT_URL}
