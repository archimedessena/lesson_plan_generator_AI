"""
URL patterns for accounts app
"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Subscription
    path('subscription/', views.subscription_management, name='subscription'),
    path('subscribe/<str:plan>/', views.initiate_payment, name='initiate_payment'),
    path('payment/verify/', views.verify_payment, name='verify_payment'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel_subscription'),
    
    # Email verification
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
]
