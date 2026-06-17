from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.http import HttpRequest
from django.shortcuts import resolve_url
from django.contrib.auth import REDIRECT_FIELD_NAME
from urllib.parse import urlparse

EXEMPT_URLS = [settings.STATIC_URL, "/accounts", "/admin", "/__reload__", "/api/v1"]


class LoginRequiredMiddleware(AuthenticationMiddleware):
    def process_request(self, request: HttpRequest) -> None:
        if request.user.is_authenticated:
            return None

        if any(request.path.startswith(url) for url in EXEMPT_URLS):
            return None

        path = request.build_absolute_uri()
        resolved_login_url = resolve_url(settings.LOGIN_URL)
        # If the login url is the same scheme and net location then just
        # use the path as the "next" url.
        login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
        current_scheme, current_netloc = urlparse(path)[:2]
        if (not login_scheme or login_scheme == current_scheme) and (
            not login_netloc or login_netloc == current_netloc
        ):
            path = request.get_full_path()
        from django.contrib.auth.views import redirect_to_login

        return redirect_to_login(path, resolved_login_url, REDIRECT_FIELD_NAME)
