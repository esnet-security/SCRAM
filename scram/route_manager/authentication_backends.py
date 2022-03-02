from django.conf import settings
from django.contrib.auth.models import Group
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class ESnetAuthBackend(OIDCAuthenticationBackend):
    def update_groups(self, user, claims):
        """Sets the users group(s) to whatever is in the claims."""

        claimed_groups = claims.get("groups", [])

        effective_groups = []
        is_admin = False

        ro_group = Group.objects.get(name="readonly")
        rw_group = Group.objects.get(name="readwrite")

        for g in claimed_groups:
            # If any of the user's groups are in DENIED_GROUPS, deny them and stop processing immediately
            if g in settings.SCRAM_DENIED_GROUPS:
                effective_groups = []
                is_admin = False
                break

            if g in settings.SCRAM_ADMIN_GROUPS:
                is_admin = True

            if g in settings.SCRAM_READONLY_GROUPS:
                if ro_group not in effective_groups:
                    effective_groups.append(ro_group)

            if g in settings.SCRAM_READWRITE_GROUPS:
                if rw_group not in effective_groups:
                    effective_groups.append(rw_group)

        user.groups.set(effective_groups)
        user.is_staff = user.is_superuser = is_admin
        user.save()

    def create_user(self, claims):
        user = super(ESnetAuthBackend, self).create_user(claims)
        return self.update_user(user, claims)

    def update_user(self, user, claims):
        user.name = claims.get("given_name", "") + " " + claims.get("family_name", "")
        user.username = claims.get("preferred_username", "")
        if claims.get("groups", False]):
            self.update_groups(user, claims)

        user.save()

        return user
