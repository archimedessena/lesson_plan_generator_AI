"""
Context processors for generator app
"""
from django.conf import settings


def site_settings(request):
    """Add site-wide settings to template context"""
    return {
        'SITE_NAME': 'LessonForge',
        'LESSONFORGE_VERSION': settings.LESSONFORGE_VERSION,
        'DEBUG': settings.DEBUG,
    }
