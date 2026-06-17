
from corsheaders.defaults import default_headers
from pathlib import Path
import os
import environ
from django.forms.renderers import TemplatesSetting
from django.utils.translation import gettext_lazy as _

env = environ.Env(DEBUG=(bool, False))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(env_file=BASE_DIR / ".env")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

if not env.bool("DEV"):
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Fixed: Added comma between hosts
ALLOWED_HOSTS = [
    "femis.sourcecognize.com",
    "afe-femis.com",
]
if env.bool("DEV"):
    ALLOWED_HOSTS += ["*", "localhost", "127.0.0.1", "10.0.2.2", "192.168.0.119"]  # Add your local IP

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 9,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    {
        "NAME": "afe.validators.AfePasswordValidator",
    },
]

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
    "corsheaders",           # ✅ Added corsheaders
    "knox",
    "rest_framework.authtoken",
    "django_tables2",
    "django_filters",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "knox.auth.TokenAuthentication",
    ),
    # ✅ Add these for mobile API support
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
}

INTERNAL_IPS = [
    "127.0.0.1",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # ✅ Moved to top (must be as high as possible)
    "django.middleware.security.SecurityMiddleware",
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

if env.bool("DEV"):
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
                "django.template.context_processors.request",
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
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": env("DB_NAME", default=os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": env("DB_USER", default=""),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default=""),
        "PORT": env("DB_PORT", default=""),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "am"  # Default to Amharic

TIME_ZONE = "Africa/Addis_Ababa"

USE_I18N = True
USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_ROOT = "media/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "core.AfeUser"


class CustomFormRenderer(TemplatesSetting):
    form_template_name = "base-form.html"


FORM_RENDERER = "afe.settings.CustomFormRenderer"

LANGUAGES = [
    ("en", _("English")),
    ("am", _("Amharic")),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

JAZZMIN_SETTINGS = {
    "language_chooser": True,
}

DEFAULT_CHARSET = "utf-8"

# ✅ CORS Configuration for Mobile App
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = list(default_headers) + [
    'token',
    'authorization',
]

# For development, allow all origins
if env.bool("DEV", default=False):
    CORS_ALLOW_ALL_ORIGINS = True
else:
    # Production: specific origins only
    CORS_ALLOWED_ORIGINS = [
        "https://afe-femis.com",
        "https://femis.sourcecognize.com",
        "exp://localhost:19000",
        "http://localhost:8081",
        "http://localhost:19000",
        "http://localhost:19006",
    ]

# ✅ CSRF exempt for API endpoints (since mobile apps can't use CSRF tokens)
if env.bool("DEV"):
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://192.168.0.119:8000",
        "http://10.0.2.2:8000",
    ]
else:
    CSRF_TRUSTED_ORIGINS = [
        "https://afe-femis.com",
        "https://femis.sourcecognize.com",
    ]
