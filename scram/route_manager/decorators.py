from django.contrib import messages
from django.shortcuts import redirect

from .views import home_page


def allowed_groups(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            group = None
            if request.user.groups.exists():
                group = request.user.groups.all()[0].name

            if group in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.add_message(
                    request,
                    messages.WARNING,
                    "You do not have permission to view the requested page",
                )
                return redirect(home_page)

        return wrapper_func

    return decorator
