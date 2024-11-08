import django

django.setup()

from scram.users.models import User  # noqa:E402

u, created = User.objects.get_or_create(username="admin")
u.set_password("password")
u.is_staff = True
u.is_superuser = True
u.save()
