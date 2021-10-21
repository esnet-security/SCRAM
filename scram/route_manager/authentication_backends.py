from django.conf import settings
from django.contrib.auth.models import Group
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class ESnetAuthBackend(OIDCAuthenticationBackend):
    def update_authorized_group(self, claims, user):
        for group in settings.SCRAM_AUTHORIZED_GROUPS:
            if group in claims.get("groups"):
                authorized_group, _ = Group.objects.get_or_create(name=group)

                if authorized_group not in user.groups.all():
                    user.groups.add(authorized_group)
                    user.save()

    def create_user(self, claims):
        user = super(ESnetAuthBackend, self).create_user(claims)
        user.name = claims.get("given_name", "") + " " + claims.get("family_name", "")
        user.username = claims.get("preferred_username", "")
        self.update_authorized_group(claims, user)
        if settings.SCRAM_ADMIN_GROUPS in claims.get("groups", []):
            user.is_staff = True
            user.is_superuser = True
        user.save()

        return user

    def update_user(self, user, claims):
        user.name = claims.get("given_name", "") + " " + claims.get("family_name", "")
        user.username = claims.get("preferred_username", "")
        self.update_authorized_group(claims, user)
        if settings.SCRAM_ADMIN_GROUPS in claims.get("groups", []):
            user.is_staff = True
            user.is_superuser = True

        return user

    def verify_claims(self, claims):
        verified = super(ESnetAuthBackend, self).verify_claims(claims)
        for group in settings.SCRAM_AUTHORIZED_GROUPS:
            if group in claims.get("groups", []):
                is_authorized = group

        return verified and is_authorized
