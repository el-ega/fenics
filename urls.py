from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.views.generic.base import TemplateView


admin.autodiscover()


urlpatterns = patterns('',
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/$', 'django.contrib.auth.views.login', name='fenics-login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login', name='fenics-logout'),
    url(r'', include('social_auth.urls')),

    ('^$', TemplateView.as_view(template_name='homepage.html')),
    ('^interior/$', TemplateView.as_view(template_name='interior.html'))
)


if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
    )