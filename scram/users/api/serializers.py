"""Serializers provide mappings between the API and the underlying model."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """This serializer defines no new fields."""

    class Meta:
        """Maps to the User model, and specifies the fields exposed by the API."""

        model = User
        fields = ["username", "name", "url"]

        extra_kwargs = {"url": {"view_name": "api:v1:user-detail", "lookup_field": "username"}}
