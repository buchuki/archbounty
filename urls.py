from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
        (r'^accounts/login/$', 'django.contrib.auth.views.login'),
        (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
        (r'^accounts/profile/$', 'accounts.views.profile'),
        (r'^admin/', include(admin.site.urls)),
)
