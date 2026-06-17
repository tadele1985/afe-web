from functools import wraps
from django.shortcuts import redirect, render
from django_htmx.http import retarget
from .models import UserRole


def role_required(role_code):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if user.userrole_set.filter(role__code__in=role_code, user=user).exists():
                return view_func(request, *args, **kwargs)
            else:
                if not request.htmx:
                    return render(request, "permission_denied.html")

                response = render(request, "permission_denied.html")
                response = retarget(response, "body")
                return response

        return _wrapped_view

    return decorator
