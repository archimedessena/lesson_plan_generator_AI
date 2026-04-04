# my_app/urls.py
from django.urls import path
from . import views


app_name = 'lesson_AI' 

urlpatterns = [
    # path(route, view_function, name)
    path('', views.index, name='index'), 
  
]