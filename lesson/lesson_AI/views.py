from django.shortcuts import render
from .models import LessonPlan
from .forms import LessonPlanForm

# Create your views here.
def index(request):
    return render(request, 'lesson_AI/index.html')


def generate_lesson_plan(request):
    if request.method == 'POST':
    
        lesson_plan = LessonPlan.objects.create(
            name_of_teacher="John Doe",
            title="Introduction to AI",
            subject="Computer Science",
            grade_level="10th Grade",
            term="Fall 2024",
            objectives="Understand the basics of AI.",
            resources="AI textbooks, online articles.",
            activities="Group discussions, hands-on projects.",
            assessment="Quizzes, project presentations."
        )
        return render(request, 'lesson_AI/lesson_plan.html', {'lesson_plan': lesson_plan})
    else:
        form = LessonPlanForm()
        return render(request, 'lesson_AI/generate_lesson_plan.html', {'form': form})
    
    
    
