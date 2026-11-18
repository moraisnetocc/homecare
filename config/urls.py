from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

def health(request):
    return JsonResponse({"status": "ok", "service": "homecore-cloud"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/v1/", include("core.api.urls")),
]
