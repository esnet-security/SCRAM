"""Define one or more custom auth backends."""

from django.conf import settings
from django.contrib.auth.models import Group
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


def groups_overlap(a, b):
    """Helper function to see if a and b have any overlap.

    Returns:
        bool: True if there's any overlap between a and b.
    """
    return not set(a).isdisjoint(b)


class ESnetAuthBackend(OIDCAuthenticationBackend):
    """Extend the OIDC backend with a custom permission model."""

    @staticmethod
    def update_groups(user, claims):
        """Set the user's group(s) to whatever is in the claims."""
        effective_groups = []
        claimed_groups = claims.get("groups", [])

        if groups_overlap(claimed_groups, settings.SCRAM_DENIED_GROUPS):
            is_admin = False
        # Don't even look at anything else if they're denied
        else:
            is_admin = groups_overlap(claimed_groups, settings.SCRAM_ADMIN_GROUPS)
            if groups_overlap(claimed_groups, settings.SCRAM_READWRITE_GROUPS):
                effective_groups.append(Group.objects.get(name="readwrite"))
            if groups_overlap(claimed_groups, settings.SCRAM_READONLY_GROUPS):
                effective_groups.append(Group.objects.get(name="readonly"))

        user.groups.set(effective_groups)
        user.is_staff = user.is_superuser = is_admin
        user.save()

    def create_user(self, claims):
        """Wrap the superclass's user creation."""  # noqa: DOC201
        user = super().create_user(claims)
        return self.update_user(user, claims)

    def update_user(self, user, claims):
        """Determine the user name from the claims and update said user's groups."""  # noqa: DOC201
        user.name = claims.get("given_name", "") + " " + claims.get("family_name", "")
        user.username = claims.get("preferred_username", "")
        if claims.get("groups", False):
            self.update_groups(user, claims)

        user.save()

        return user
