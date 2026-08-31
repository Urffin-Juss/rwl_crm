from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from django.contrib.auth import views as auth_views

from apps.webui import views as webui_views


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', webui_views.landing, name='landing'),
    path('workspace/', webui_views.workspace, name='workspace'),
    path('workspace/mobile/', webui_views.mobile_workspace, name='mobile_workspace'),

    path('login/', auth_views.LoginView.as_view(template_name='webui/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),


    path('api/', include('apps.events.urls')),

    path('', include('apps.webui.urls')),

    path('api/', include('apps.miniapp.urls')),

    path("legal/", include("apps.legal.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
