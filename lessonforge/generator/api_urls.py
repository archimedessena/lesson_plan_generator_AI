"""
API URL patterns for generator app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import LessonPlanViewSet, TemplateViewSet, FeedbackViewSet

router = DefaultRouter()
router.register(r'lesson-plans', LessonPlanViewSet, basename='lessonplan')
router.register(r'templates', TemplateViewSet, basename='template')
router.register(r'feedback', FeedbackViewSet, basename='feedback')

urlpatterns = [
    path('', include(router.urls)),
]
