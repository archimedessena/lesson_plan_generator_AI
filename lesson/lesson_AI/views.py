from django.shortcuts import render
from .models import LessonPlan

# Create your views here.
def index(request):
    return render(request, 'lesson_AI/index.html')


def generate_lesson_plan(request):
    if request.method == 'POST':
        # Here you would handle the form submission and generate the lesson plan
        # For now, we'll just create a dummy lesson plan
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
        return render(request, 'lesson_AI/generate_lesson_plan.html')