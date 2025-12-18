from django.contrib.auth.apps import AuthConfig


class CustomAuthConfig(AuthConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django.contrib.auth"
    verbose_name = "102. Alpha Auth"
