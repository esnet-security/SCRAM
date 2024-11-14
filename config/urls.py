from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.views import defaults as default_views
from rest_framework.authtoken.views import obtain_auth_token

from .api_router import app_name

urlpatterns = [
    # Route Manager urls
    path("", include("scram.route_manager.urls", namespace="route_manager")),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("scram.users.urls", namespace="users")),
    # Your stuff: custom urls includes go here
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    # Static file serving when using Gunicorn + Uvicorn for local web socket development
    urlpatterns += staticfiles_urlpatterns()

# OIDC is only set up to work on staging/production hosts. Locally, we are not connected to the OIDC server
if settings.AUTH_METHOD == "oidc":
    # Flake8 doesn't like this as it's an "unused import" but you have to call the include urls as a string
    # so we ignore flake8 on this one
    import mozilla_django_oidc  # noqa: F401

    urlpatterns += [path("oidc/", include("mozilla_django_oidc.urls"))]
elif settings.AUTH_METHOD == "local":
    urlpatterns += [path("auth/", include("scram.local_auth.urls", namespace="local_auth"))]
# API URLS
api_version_urls = (
    [
        path("v1/", include("config.api_router", namespace="v1")),
    ],
    app_name,
)
urlpatterns += [
    # API base url
    path("api/", include(api_version_urls, namespace="api")),
    # DRF auth token
    path("auth-token/", obtain_auth_token),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
