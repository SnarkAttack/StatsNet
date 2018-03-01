from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from StatsNet import settings

urlpatterns = [
    url(r'^games/', include('games.urls', namespace='games')),
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/login/', auth_views.login, name='login'),
    url(r'^acounts/logout/', auth_views.logout, {'next_page': '/login/'}, name='logout'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()
