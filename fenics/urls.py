from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
    path('', include('ega.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
