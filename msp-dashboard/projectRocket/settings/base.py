import os
from pathlib import Path
from django.contrib.messages import constants as messages
from dotenv import load_dotenv
from celery.schedules import crontab

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent

SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-j%^*y0krq5^-#3lggoecxw!d7ad_gqkab3t5w17&0w06+qf8+8"
)

DEBUG = os.environ.get("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

DIGITAL_OCEAN_EXTERNAL_HOSTNAME = os.environ.get("DIGITAL_OCEAN_EXTERNAL_HOSTNAME")
if DIGITAL_OCEAN_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(DIGITAL_OCEAN_EXTERNAL_HOSTNAME)

# CSRF_TRUSTED_ORIGINS in .env will be a string of comma separated values
CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS", "http://127.0.0.1:8000,http://157.230.230.23"
).split(
    ","
)  # Split by comma


SHARED_APPS = [
    "django_tenants",
    "rest_framework.authtoken",
    "rest_framework",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "ckeditor",
    "ckeditor_uploader",
    "mathfilters",
    "crispy_forms",
    "recurrence",
    "crispy_bootstrap4",  # Crispy Forms
    "social_django",
    "django_extensions",
    # authentication apps
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_email",
    "two_factor",
    "two_factor.plugins.email",
    "multiselectfield",
    "phonenumber_field",
    "auditlog",
    "accounts",
    "apps",
    "calendar_event",
    "chat",
    "taggit",
    "djstripe",
    "tenants",
    "django_celery_beat",
    "atlas",
]

TENANT_APPS = [
    "rest_framework.authtoken",
    "rest_framework",
    "auditlog",
    "accounts",
    "apps",
    "chat",
    "dashboards",
    "djstripe",
    "calendar_event",
    "layouts",
    "pages",
    "taggit",
    "atlas",
]

INSTALLED_APPS = SHARED_APPS + [app for app in TENANT_APPS if app not in SHARED_APPS]

TENANT_MODEL = "tenants.MspCompany"
TENANT_DOMAIN_MODEL = "tenants.Domain"

SHOW_PUBLIC_IF_NO_TENANT_FOUND = True

MIDDLEWARE = [
    # "allauth.account.middleware.AccountMiddleware",
    "django_tenants.middleware.main.TenantMainMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
    "pages.middleware.PasswordUpdateWarningMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
    "apps.middlware.ClientThresholdMiddleware",
    "apps.middlware.EnforceTwoFactorMiddleware",
]

ROOT_URLCONF = "projectRocket.urls"
PUBLIC_SCHEMA_URLCONF = "projectRocket.urls_public"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "apps.context_processors.active_entry",
                "apps.context_processors.integrations",
                "rbac.context_processors.subscription_context",
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
    "social_core.backends.google.GoogleOAuth2",
]

CRISPY_TEMPLATE_PACK = "bootstrap4"
WSGI_APPLICATION = "projectRocket.wsgi.application"

DB_NAME = os.environ.get("DB_NAME", "postgres")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "1234")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}

DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

DATABASE_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = ("static",)

DEFAULT_FILE_STORAGE = "django_tenants.files.storage.TenantFileSystemStorage"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")  # configuration for render
MEDIA_URL = "/media/"
CKEDITOR_UPLOAD_PATH = "uploads/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MESSAGE_TAGS = {
    messages.DEBUG: "alert-info",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}

AUTH_USER_MODEL = "accounts.MSPAuthUser"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = os.getenv("EMAIL_PORT", 587)
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", True)

PHONENUMBER_DB_FORMAT = "NATIONAL"
PHONENUMBER_DEFAULT_REGION = "US"

STRIPE_PUBLISH_KEY = os.environ.get("STRIPE_TEST_PUBLIC_KEY", "")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_TEST_SECRET_KEY", "")
STRIPE_TEST_PUBLISH_KEY = os.environ.get("STRIPE_TEST_PUBLIC_KEY", "")
STRIPE_TEST_SECRET_KEY = os.environ.get("STRIPE_TEST_SECRET_KEY", "")
STRIPE_LIVE_MODE = False
DJSTRIPE_WEBHOOK_SECRET = os.environ.get("DJSTRIPE_WEBHOOK_SECRET", "")
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"

API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", "True") == "True"

ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIAL_AUTH_URL_NAMESPACE = "social"
SOCIAL_AUTH_LOGIN_ERROR_URL = "/account/login"

ACCOUNT_FORMS = {
    "login": "projectRocket.forms.UserLoginForm",
    "signup": "projectRocket.forms.UserRegistrationForm",
    "change_password": "projectRocket.forms.PasswordChangeForm",
    "set_password": "projectRocket.forms.PasswordSetForm",
    "reset_password": "projectRocket.forms.PasswordResetForm",
    "reset_password_from_key": "projectRocket.forms.PasswordResetKeyForm",
}

SOCIALACCOUNT_QUERY_EMAIL = True

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get(
    "SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", ""
)

SITE_ID = 1

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("apps.token.TokenUserAuthentication",),
}

PHONENUMBER_DB_FORMAT = "INTERNATIONAL"
PHONENUMBER_DEFAULT_FORMAT = "INTERNATIONAL"
PHONENUMBER_DEFAULT_REGION = None

# Quickbooks keys & credentials
QUICKBOOKS_CLIENT_ID = os.environ.get("QUICKBOOKS_CLIENT_ID")
QUICKBOOKS_CLIENT_SECRET = os.environ.get("QUICKBOOKS_CLIENT_SECRET")
QUICKBOOKS_REDIRECT_CALLBACK_URL = os.environ.get("QUICKBOOKS_REDIRECT_CALLBACK_URL")
QUICKBOOKS_ENVIRONMENT = os.environ.get("QUICKBOOKS_ENVIRONMENT")
QUICKBOOKS_BASE_URL = os.environ.get("QUICKBOOKS_BASE_SANDBOX")

# Celery Beat Configuration
CELERY_BEAT_SCHEDULE = {
    "refresh-quickbooks-tokens": {
        "task": "apps.tasks.refresh_quickbooks_tokens",
        "schedule": crontab(hour=23, minute=0),
    },
}

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL")

# Cache Configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL"),
    }
}

# Two-Factor Authentication Settings
TWO_FACTOR_CALL_GATEWAY = "two_factor.gateways.fake.Fake"
TWO_FACTOR_SMS_GATEWAY = "two_factor.gateways.fake.Fake"
TWO_FACTOR_EMAIL_GATEWAY = "two_factor.gateways.email.Email"

# 2FA Login Settings
TWO_FACTOR_LOGIN_DISABLED = False
TWO_FACTOR_REMEMBER_COOKIE_AGE = 30 * 24 * 60 * 60  # 30 days
TWO_FACTOR_REMEMBER_COOKIE_NAME = "remember_2fa"

# 2FA Device Settings
TWO_FACTOR_TOTP_ISSUER = "MSP Dashboard"
TWO_FACTOR_TOTP_DIGITS = 6
TWO_FACTOR_TOTP_PERIOD = 30

# 2FA Backup Codes
TWO_FACTOR_BACKUP_CODES_COUNT = 10
TWO_FACTOR_BACKUP_CODES_LENGTH = 10

# 2FA Email Settings
TWO_FACTOR_EMAIL_TEMPLATE = "two_factor/email/token_email.html"
TWO_FACTOR_EMAIL_SUBJECT = "Your verification code"

# 2FA QR Code Settings
TWO_FACTOR_QR_FACTORY = "qrcode.image.pil.PilImage"

# 2FA Integration Settings
TWO_FACTOR_FORCE_OTP_ADMIN = False
TWO_FACTOR_LOGIN_TIMEOUT = 600  # 10 minutes

LOGIN_URL = "two_factor:login"
LOGIN_REDIRECT_URL = "/"

OTP_EMAIL_SUBJECT = "MSP Dashboard Verification"
OTP_EMAIL_BODY_HTML_TEMPLATE_PATH = "two_factor/email/2fa_code_email.html"
