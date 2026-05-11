"""Register ourselves with Django."""

from django.apps import AppConfig


class RouteManagerConfig(AppConfig):
    """Define the name of the module that's the main app."""

    name = "scram.route_manager"
