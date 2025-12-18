import re
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path, include
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from alpha.settings import API_URL_PREFIX, VITE_OP_TYPE

urlpatterns = [
    path(API_URL_PREFIX + "jet/", include("jet.urls", "jet")),
    path(API_URL_PREFIX + "admin/", admin.site.urls),
    path(API_URL_PREFIX + "django-rq/", include("django_rq.urls")),
    path(API_URL_PREFIX + "api/alpha/", include("apps.alpha_base.urls")),
    path(API_URL_PREFIX + "api/auth/", include("apps.alpha_auth.urls")),
    path(API_URL_PREFIX + "api/log/", include("apps.alpha_log.urls")),
    path(API_URL_PREFIX + "api/test/", include("apps.alpha_test.urls")),
    path(API_URL_PREFIX + "api/example/", include("apps.alpha_example.urls")),
    # path(API_URL_PREFIX + "api/rubicon/", include("apps.rubicon.urls")),
    path(API_URL_PREFIX + "api/rubicon/", include("apps.rubicon_v3.urls")),
    path(API_URL_PREFIX + "api/rubicon_admin/", include("apps.rubicon_admin.urls")),
    # path(API_URL_PREFIX + "api/rubicon_data/", include("apps.rubicon_data.urls")),
    re_path(
        re.escape(API_URL_PREFIX) + r".*$",
        TemplateView.as_view(template_name="index.html"),
        name="app",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
