from .base import *
import dj_database_url

DEBUG = True


DATABASE_URL = os.environ.get("DATABASE_URL", DATABASE_URL)

DATABASES = {"default": dj_database_url.config(default=DATABASE_URL, conn_max_age=600)}

DATABASES["default"]["ENGINE"] = ("django_tenants.postgresql_backend",)
DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)


STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# MIDDLEWARE = [ "debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]
# SHARED_APPS += ['debug_toolbar']

INSTALLED_APPS = SHARED_APPS + [app for app in TENANT_APPS if app not in SHARED_APPS]

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

X_FRAME_OPTIONS = "ALLOWALL"
