from functools import wraps

from django.http import HttpResponseForbidden


def roles_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Authentication required.")
            if request.user.role not in roles:
                return HttpResponseForbidden("You do not have access to this resource.")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
