from django.conf import settings
from django.contrib.auth.models import Group
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class ESnetAuthBackend(OIDCAuthenticationBackend):
    def update_authorized_group(self, claims, user):
        if settings.SCRAM_AUTHORIZED_GROUPS in claims.get("groups"):
            authorized_group, _ = Group.objects.get_or_create(
                name=settings.SCRAM_AUTHORIZED_GROUPS
            )

            if authorized_group not in user.groups.all():
                user.groups.add(authorized_group)
                user.save()

    def create_user(self, claims):
        user = super(ESnetAuthBackend, self).create_user(claims)
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        print(f"user: {user}, claims: {claims}")
        self.update_authorized_group(claims, user)
        user.save()

        return user

    def update_user(self, user, claims):
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        print(f"user: {user}, claims: {claims}")
        self.update_authorized_group(claims, user)
        user.save()

        return user

    def verify_claims(self, claims):
        verified = super(ESnetAuthBackend, self).verify_claims(claims)
        is_authorized = settings.SCRAM_AUTHORIZED_GROUPS in claims.get("groups", [])
        is_staff = settings.SCRAM_AUTHORIZED_GROUPS in claims.get("groups", [])
        return verified and is_authorized and is_staff
