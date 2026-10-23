from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("predictions.urls")),
    path("api/health/", lambda request: JsonResponse({"status":"ok","service":"rice-guard-api"})),
    path("api/csrf/", ensure_csrf_cookie(lambda request: JsonResponse({"detail":"CSRF cookie set"}))),
]
