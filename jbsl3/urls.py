import os

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("app.urls")),
    path("accounts/", include("allauth.urls")),
]


if os.path.exists("local.py"):
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
