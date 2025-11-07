from pathlib import Path
import environ
import os
from datetime import timedelta

env = environ.Env(DEBUG=(bool, False))
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
# SECRET_KEY = env("SECRET_KEY", default="django-insecure-default-key")

# SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
# ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS").split(",")



BASE_DIR = Path(__file__).resolve().parent.parent




SECRET_KEY = 'django-insecure-8%nwg5did=_-(bz#ow8qgn848ouzws0n5cn=wd4**rbso$52^^'


DEBUG = True

ALLOWED_HOSTS = ['*']




INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    "rest_framework",
    "drf_spectacular",
    # "assignments",

    "assignments.apps.AssignmentsConfig",
]




REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


SPECTACULAR_SETTINGS = {
    "TITLE": "AI Task Assignment API",
    "DESCRIPTION": "API for AI-based internal assignment system",
    "VERSION": "1.0.0",
}

# # Email config
# EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
# EMAIL_HOST = env("EMAIL_HOST", "smtp.gmail.com")
# EMAIL_PORT = int(env("EMAIL_PORT", 587))
# EMAIL_USE_TLS = env("EMAIL_USE_TLS", "True") == "True"
# EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
# EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
# DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

# # Controls
# ENABLE_EMAIL_NOTIFICATIONS = env("ENABLE_EMAIL_NOTIFICATIONS", "true") == "true"
# USE_CELERY_FOR_EMAIL = env("USE_CELERY_FOR_EMAIL", "false") == "true"


EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default="True") == "True"
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)

ENABLE_EMAIL_NOTIFICATIONS = env("ENABLE_EMAIL_NOTIFICATIONS", default="true") == "true"
USE_CELERY_FOR_EMAIL = env("USE_CELERY_FOR_EMAIL", default="false") == "true"






# SLACK_SIGNING_SECRET = config("SLACK_SIGNING_SECRET", default="")
# SLACK_BOT_TOKEN = config("SLACK_BOT_TOKEN", default="")

# Slack
SLACK_SIGNING_SECRET = env("SLACK_SIGNING_SECRET", default="")
SLACK_BOT_TOKEN = env("SLACK_BOT_TOKEN", default="")


# LLM provider keys available from env
OPENAI_API_KEY = env("OPENAI_API_KEY", default=None)
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default=None)

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True


ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        # 'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'



# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT"),
    }
}



AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]



LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "ALGORITHM": "HS256",
    # ... other settings optional
}

SPECTACULAR_SETTINGS = {
    "TITLE": "AI Task Assignment API",
    "DESCRIPTION": "API for AI-based internal assignment system",
    "VERSION": "1.0.0",
    "COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
    "SECURITY": [{"BearerAuth": []}],
}


# Celery Configuration
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Kolkata"

# CELERY_BROKER_USE_SSL = {"ssl_cert_reqs": "CERT_NONE"}
# CELERY_REDIS_BACKEND_USE_SSL = {"ssl_cert_reqs": "CERT_NONE"}
