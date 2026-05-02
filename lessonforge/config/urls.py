"""
LessonForge URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Main apps
    path('', include('generator.urls')),
    path('accounts/', include('accounts.urls')),
    
    # API
    path('api/', include('generator.api_urls')),
    path('api/auth/', include('accounts.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass

# Custom error handlers
handler404 = 'generator.views.custom_404'
handler500 = 'generator.views.custom_500'
