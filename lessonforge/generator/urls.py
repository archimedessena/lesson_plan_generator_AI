"""
URL patterns for generator app
"""
from django.urls import path
from . import views

app_name = 'generator'

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Lesson plan generation
    path('generate/', views.generate_lesson_plan, name='generate'),
    
    # Lesson plan management
    path('my-plans/', views.my_lesson_plans, name='my_lesson_plans'),
    path('plan/<uuid:uuid>/', views.lesson_plan_detail, name='lesson_plan_detail'),
    path('plan/<uuid:uuid>/download/', views.download_pdf, name='download_pdf'),
    path('plan/<uuid:uuid>/delete/', views.delete_lesson_plan, name='delete_lesson_plan'),
    path('plan/<uuid:uuid>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('plan/<uuid:uuid>/share/', views.share_lesson_plan, name='share_lesson_plan'),
    path('plan/<uuid:uuid>/feedback/', views.submit_feedback, name='submit_feedback'),
    
    # Public sharing
    path('share/<str:token>/', views.shared_lesson_plan_view, name='shared_lesson_plan'),
    
    # Templates
    path('templates/', views.templates_list, name='templates'),
    
    # Pricing
    path('pricing/', views.pricing, name='pricing'),
]
