"""
Main views for LessonForge generator app
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile

from .models import LessonPlan, Template, UsageLog, SharedLessonPlanView, Feedback
from .forms import LessonPlanGenerationForm, FeedbackForm
from .services import lesson_plan_generator
from .pdf_service import pdf_generator
import logging
import json

logger = logging.getLogger('lessonforge')


def home(request):
    """Homepage view"""
    context = {
        'total_plans': LessonPlan.objects.count(),
        'total_users': settings.AUTH_USER_MODEL.objects.filter(is_active=True).count(),
    }
    return render(request, 'generator/home.html', context)


@login_required
def dashboard(request):
    """User dashboard view"""
    user = request.user
    
    # Get user's recent lesson plans
    recent_plans = LessonPlan.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Get statistics
    total_plans = LessonPlan.objects.filter(user=user).count()
    
    # Calculate monthly usage
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_usage = LessonPlan.objects.filter(
        user=user,
        created_at__gte=month_start
    ).count()
    
    # Get usage percentage
    monthly_limit = user.monthly_limit
    usage_percentage = (monthly_usage / monthly_limit * 100) if monthly_limit > 0 else 0
    
    context = {
        'recent_plans': recent_plans,
        'total_plans': total_plans,
        'monthly_usage': monthly_usage,
        'monthly_limit': monthly_limit,
        'usage_percentage': usage_percentage,
        'can_generate': user.can_generate_lesson_plan(),
        'subscription_tier': user.subscription_tier,
        'has_active_subscription': user.has_active_subscription,
    }
    
    return render(request, 'generator/dashboard.html', context)


@login_required
def generate_lesson_plan(request):
    """Generate a new lesson plan"""
    
    # Check if user can generate
    if not request.user.can_generate_lesson_plan():
        messages.error(request, 'You have reached your monthly limit. Please upgrade your plan to generate more lesson plans.')
        return redirect('generator:pricing')
    
    if request.method == 'POST':
        form = LessonPlanGenerationForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                # Extract form data
                subject = form.cleaned_data['subject']
                topic = form.cleaned_data['topic']
                grade_level = form.cleaned_data['grade_level']
                curriculum = form.cleaned_data['curriculum']
                duration = form.cleaned_data['duration']
                objectives = form.cleaned_data['learning_objectives']
                additional_requirements = form.cleaned_data.get('additional_requirements', '')
                
                # Get template if selected
                template = None
                template_id = form.cleaned_data.get('template')
                if template_id:
                    try:
                        template = Template.objects.get(id=template_id)
                        # Increment usage count
                        template.usage_count += 1
                        template.save(update_fields=['usage_count'])
                    except Template.DoesNotExist:
                        pass
                
                # Generate lesson plan using AI
                content, metadata = lesson_plan_generator.generate_lesson_plan(
                    subject=subject,
                    topic=topic,
                    grade_level=grade_level,
                    curriculum=curriculum,
                    duration=duration,
                    objectives=objectives,
                    additional_requirements=additional_requirements,
                    template=template
                )
                
                # Create lesson plan object
                lesson_plan = LessonPlan.objects.create(
                    user=request.user,
                    template=template,
                    subject=subject,
                    topic=topic,
                    grade_level=grade_level,
                    curriculum=curriculum,
                    duration=duration,
                    learning_objectives=objectives,
                    additional_requirements=additional_requirements,
                    content=content,
                    generation_time=metadata['generation_time']
                )
                
                # Log usage
                UsageLog.objects.create(
                    user=request.user,
                    lesson_plan=lesson_plan,
                    input_tokens=metadata['input_tokens'],
                    output_tokens=metadata['output_tokens'],
                    total_tokens=metadata['total_tokens'],
                    estimated_cost=metadata['estimated_cost'],
                    response_time=metadata['generation_time']
                )
                
                # Generate PDF in background would be ideal, but for now do it synchronously
                try:
                    pdf_buffer = pdf_generator.generate_pdf(lesson_plan)
                    pdf_filename = f"lesson_plan_{lesson_plan.uuid}.pdf"
                    lesson_plan.pdf_file.save(
                        pdf_filename,
                        ContentFile(pdf_buffer.getvalue()),
                        save=True
                    )
                except Exception as e:
                    logger.error(f"Error generating PDF: {str(e)}")
                    # Continue even if PDF generation fails
                
                messages.success(request, 'Lesson plan generated successfully!')
                return redirect('generator:lesson_plan_detail', uuid=lesson_plan.uuid)
                
            except Exception as e:
                logger.error(f"Error generating lesson plan: {str(e)}")
                messages.error(request, f'An error occurred while generating the lesson plan: {str(e)}')
                return render(request, 'generator/generate.html', {'form': form})
    else:
        form = LessonPlanGenerationForm(user=request.user)
    
    # Get available templates
    templates = Template.objects.filter(is_public=True)
    if not request.user.has_active_subscription:
        templates = templates.filter(is_premium=False)
    
    context = {
        'form': form,
        'templates': templates,
    }
    
    return render(request, 'generator/generate.html', context)


@login_required
def lesson_plan_detail(request, uuid):
    """View a specific lesson plan"""
    lesson_plan = get_object_or_404(
        LessonPlan,
        uuid=uuid,
        user=request.user
    )
    
    # Get feedback if exists
    feedback = Feedback.objects.filter(
        user=request.user,
        lesson_plan=lesson_plan
    ).first()
    
    context = {
        'lesson_plan': lesson_plan,
        'feedback': feedback,
    }
    
    return render(request, 'generator/lesson_plan_detail.html', context)


@login_required
def my_lesson_plans(request):
    """List all user's lesson plans with search and filter"""
    
    # Get query parameters
    search = request.GET.get('search', '')
    curriculum = request.GET.get('curriculum', '')
    subject = request.GET.get('subject', '')
    sort = request.GET.get('sort', '-created_at')
    
    # Base queryset
    plans = LessonPlan.objects.filter(user=request.user)
    
    # Apply filters
    if search:
        plans = plans.filter(
            Q(title__icontains=search) |
            Q(topic__icontains=search) |
            Q(subject__icontains=search)
        )
    
    if curriculum:
        plans = plans.filter(curriculum=curriculum)
    
    if subject:
        plans = plans.filter(subject__icontains=subject)
    
    # Apply sorting
    valid_sorts = ['title', '-title', 'created_at', '-created_at', 'subject', '-subject']
    if sort in valid_sorts:
        plans = plans.order_by(sort)
    else:
        plans = plans.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(plans, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique subjects for filter
    subjects = LessonPlan.objects.filter(user=request.user).values_list('subject', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'subjects': subjects,
        'search': search,
        'curriculum': curriculum,
        'subject': subject,
        'sort': sort,
    }
    
    return render(request, 'generator/my_lesson_plans.html', context)


@login_required
def download_pdf(request, uuid):
    """Download PDF of a lesson plan"""
    lesson_plan = get_object_or_404(
        LessonPlan,
        uuid=uuid,
        user=request.user
    )
    
    if not lesson_plan.pdf_file:
        messages.error(request, 'PDF file not available for this lesson plan.')
        return redirect('generator:lesson_plan_detail', uuid=uuid)
    
    # Serve file
    response = HttpResponse(lesson_plan.pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="lesson_plan_{lesson_plan.uuid}.pdf"'
    
    return response


@login_required
def delete_lesson_plan(request, uuid):
    """Delete a lesson plan"""
    lesson_plan = get_object_or_404(
        LessonPlan,
        uuid=uuid,
        user=request.user
    )
    
    if request.method == 'POST':
        lesson_plan.delete()
        messages.success(request, 'Lesson plan deleted successfully.')
        return redirect('generator:my_lesson_plans')
    
    return render(request, 'generator/confirm_delete.html', {'lesson_plan': lesson_plan})


@login_required
def toggle_favorite(request, uuid):
    """Toggle favorite status of a lesson plan"""
    lesson_plan = get_object_or_404(
        LessonPlan,
        uuid=uuid,
        user=request.user
    )
    
    lesson_plan.is_favorite = not lesson_plan.is_favorite
    lesson_plan.save(update_fields=['is_favorite'])
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_favorite': lesson_plan.is_favorite})
    
    return redirect('generator:lesson_plan_detail', uuid=uuid)


@login_required
def share_lesson_plan(request, uuid):
    """Generate shareable link for lesson plan"""
    lesson_plan = get_object_or_404(
        LessonPlan,
        uuid=uuid,
        user=request.user
    )
    
    if not lesson_plan.is_shared:
        lesson_plan.is_shared = True
        lesson_plan.save()
    
    share_url = request.build_absolute_uri(lesson_plan.share_url)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'share_url': share_url})
    
    context = {'lesson_plan': lesson_plan, 'share_url': share_url}
    return render(request, 'generator/share_lesson_plan.html', context)


def shared_lesson_plan_view(request, token):
    """Public view for shared lesson plans"""
    lesson_plan = get_object_or_404(LessonPlan, share_token=token, is_shared=True)
    
    # Log the view
    ip_address = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    SharedLessonPlanView.objects.create(
        lesson_plan=lesson_plan,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    context = {'lesson_plan': lesson_plan}
    return render(request, 'generator/shared_lesson_plan.html', context)


@login_required
def submit_feedback(request, uuid):
    """Submit feedback for a lesson plan"""
    lesson_plan = get_object_or_404(
        LessonPlan,
        uuid=uuid,
        user=request.user
    )
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        
        if form.is_valid():
            feedback, created = Feedback.objects.update_or_create(
                user=request.user,
                lesson_plan=lesson_plan,
                defaults={
                    'rating': form.cleaned_data['rating'],
                    'quality_rating': form.cleaned_data.get('quality_rating'),
                    'relevance_rating': form.cleaned_data.get('relevance_rating'),
                    'structure_rating': form.cleaned_data.get('structure_rating'),
                    'comment': form.cleaned_data.get('comment', ''),
                }
            )
            
            messages.success(request, 'Thank you for your feedback!')
            return redirect('generator:lesson_plan_detail', uuid=uuid)
    
    return redirect('generator:lesson_plan_detail', uuid=uuid)


def templates_list(request):
    """List available templates"""
    templates = Template.objects.filter(is_public=True)
    
    # Filter by curriculum if specified
    curriculum = request.GET.get('curriculum')
    if curriculum:
        templates = templates.filter(Q(curriculum=curriculum) | Q(curriculum='ALL'))
    
    # Filter by subject if specified
    subject = request.GET.get('subject')
    if subject:
        templates = templates.filter(Q(subject=subject) | Q(subject='GENERAL'))
    
    context = {
        'templates': templates,
        'curriculum': curriculum,
        'subject': subject,
    }
    
    return render(request, 'generator/templates.html', context)


def pricing(request):
    """Pricing page"""
    context = {
        'free_limit': settings.LESSONFORGE_FREE_PLAN_LIMIT,
        'teacher_limit': settings.LESSONFORGE_TEACHER_PLAN_LIMIT,
        'teacher_price': settings.LESSONFORGE_TEACHER_PLAN_PRICE / 100,  # Convert from pesewas
        'school_price': settings.LESSONFORGE_SCHOOL_PLAN_PRICE / 100,
    }
    return render(request, 'generator/pricing.html', context)


# Error handlers
def custom_404(request, exception):
    """Custom 404 error page"""
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    """Custom 500 error page"""
    return render(request, 'errors/500.html', status=500)
