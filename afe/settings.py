from corsheaders.defaults import default_headers
import dj_database_url
from pathlib import Path
import os
import environ
from django.forms.renderers import TemplatesSetting
from django.utils.translation import gettext_lazy as _

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(env_file=BASE_DIR / ".env")

# Secret key
SECRET_KEY = env.str("SECRET_KEY", default="your-local-dev-key")

# Debug
DEBUG = env.bool("DEBUG", default=False)
DEV = env.bool("DEV", default=False)
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Hosts
ALLOWED_HOSTS = ['https://afe-femis-rl4h.onrender.com','127.0.0.1']

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

if DEV:
    ALLOWED_HOSTS += ["*", "localhost", "127.0.0.1", "10.0.2.2", "192.168.0.119"]

# Security (production only)
DEBUG = True
if not DEV:
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Application definition
INSTALLED_APPS = [
    "core.apps.CoreConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.forms",
    "slippers",
    "django.contrib.staticfiles",
    "django_htmx",
    "django_browser_reload",
    "rest_framework",
    "corsheaders",
    "knox",
    "rest_framework.authtoken",
    "django_tables2",
    "django_filters",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.LoginRequiredMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]


if DEV:
    MIDDLEWARE.append("django_browser_reload.middleware.BrowserReloadMiddleware")

ROOT_URLCONF = "afe.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.sidebar_content",
            ],
            "builtins": ["slippers.templatetags.slippers", "django.templatetags.i18n"],
        },
    },
]

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"
WSGI_APPLICATION = "afe.wsgi.application"

# Database
if os.environ.get('DATABASE_URL'):
   DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True,
    )
}
else:
    DATABASES = {
        "default": {
            "ENGINE": env("DB_ENGINE", default="django.db.backends.sqlite3"),
            "NAME": env("DB_NAME", default=str(BASE_DIR / "db.sqlite3")),
            "USER": env("DB_USER", default=""),
            "PASSWORD": env("DB_PASSWORD", default=""),
            "HOST": env("DB_HOST", default=""),
            "PORT": env("DB_PORT", default=""),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 9}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "afe.validators.AfePasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "am"
TIME_ZONE = "Africa/Addis_Ababa"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ("en", _("English")),
    ("am", _("Amharic")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

# Static files
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_ROOT = "media/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "core.AfeUser"

INTERNAL_IPS = ["127.0.0.1"]

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("knox.auth.TokenAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
}

# CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = list(default_headers) + ['token', 'authorization']

if DEV:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = [
        "https://afe-femis.com",
        "https://femis.sourcecognize.com",
        "exp://localhost:19000",
        "http://localhost:8081",
    ]

# CSRF
if DEV:
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
]
else:
    CSRF_TRUSTED_ORIGINS = [
        "https://afe-femis.com",
        "https://femis.sourcecognize.com",
        "https://afe-femis-rl4h.onrender.com",
]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Forms
class CustomFormRenderer(TemplatesSetting):
    form_template_name = "base-form.html"

FORM_RENDERER = "afe.settings.CustomFormRenderer"

JAZZMIN_SETTINGS = {"language_chooser": True}
DEFAULT_CHARSET = "utf-8"