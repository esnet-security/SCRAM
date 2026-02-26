"""Views provide mappings between the underlying model and how they're listed in the API."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .serializers import UserSerializer

User = get_user_model()


class UserViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    """Lookup Users by username."""

    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "username"

    def get_queryset(self, *args, **kwargs):
        """Query on User ID."""
        return self.queryset.filter(id=self.request.user.id)

    @staticmethod
    @action(detail=False, methods=["GET"])
    def me(request):
        """Return the current user."""
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)
