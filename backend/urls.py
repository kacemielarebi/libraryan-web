from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from api.views import FrontendAppView
import os
from django.views.static import serve
import os

REACT_BUILD_DIR = os.path.join(settings.BASE_DIR, 'frontend_build')

urlpatterns = [
    path('api/', include('api.urls')),
]

# ✅ لخدمة ملفات React (CSS / JS)
urlpatterns += [

    re_path(r'^(?P<path>(favicon\.ico|logo192\.png|manifest\.json))$', serve, {
        'document_root': REACT_BUILD_DIR,
    }),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# ✅ هذا يجب أن يكون الأخير
urlpatterns += [
    re_path(r'^.*$', FrontendAppView.as_view(), name='home'),
]