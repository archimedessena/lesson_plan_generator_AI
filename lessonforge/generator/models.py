"""
Generator app models - LessonPlan, Template, Usage tracking
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
import uuid


class Template(models.Model):
    """Lesson plan templates"""
    
    CURRICULUM_CHOICES = [
        ('IGCSE', 'Cambridge IGCSE'),
        ('A_LEVEL', 'Cambridge A-Level'),
        ('WASSCE', 'WASSCE'),
        ('ALL', 'All Curricula'),
    ]
    
    SUBJECT_CHOICES = [
        ('MATHEMATICS', 'Mathematics'),
        ('SCIENCE', 'Science'),
        ('ENGLISH', 'English'),
        ('LANGUAGES', 'Languages'),
        ('HUMANITIES', 'Humanities'),
        ('ARTS', 'Arts'),
        ('TECHNICAL', 'Technical/Vocational'),
        ('GENERAL', 'General'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    curriculum = models.CharField(max_length=20, choices=CURRICULUM_CHOICES)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    
    # Template structure (JSON)
    structure = models.JSONField(default=dict, help_text="Template sections and components")
    
    # AI prompt customization
    system_prompt_addition = models.TextField(blank=True, help_text="Additional context for AI generation")
    
    # Access control
    is_public = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False, help_text="Requires paid subscription")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_templates')
    
    # Usage stats
    usage_count = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'templates'
        ordering = ['-usage_count', 'name']
        indexes = [
            models.Index(fields=['curriculum', 'subject']),
            models.Index(fields=['is_public', 'is_premium']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class LessonPlan(models.Model):
    """Generated lesson plans"""
    
    CURRICULUM_CHOICES = [
        ('IGCSE', 'Cambridge IGCSE'),
        ('A_LEVEL', 'Cambridge A-Level'),
        ('WASSCE', 'WASSCE'),
    ]
    
    # Identifiers
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_plans')
    template = models.ForeignKey(Template, on_delete=models.SET_NULL, null=True, blank=True, related_name='lesson_plans')
    
    # Lesson details
    title = models.CharField(max_length=300)
    subject = models.CharField(max_length=100)
    topic = models.CharField(max_length=300)
    grade_level = models.CharField(max_length=50)
    curriculum = models.CharField(max_length=20, choices=CURRICULUM_CHOICES)
    duration = models.IntegerField(help_text="Duration in minutes")
    
    # Input data
    learning_objectives = models.TextField()
    additional_requirements = models.TextField(blank=True)
    
    # Generated content
    content = models.TextField(help_text="Full lesson plan content")
    
    # PDF file
    pdf_file = models.FileField(upload_to='lesson_plans/', blank=True, null=True)
    
    # Metadata
    is_favorite = models.BooleanField(default=False)
    generation_time = models.FloatField(default=0, help_text="Time taken to generate in seconds")
    
    # Sharing
    share_token = models.CharField(max_length=100, unique=True, blank=True, null=True)
    is_shared = models.BooleanField(default=False)
    shared_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lesson_plans'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['curriculum', 'subject']),
            models.Index(fields=['share_token']),
            models.Index(fields=['uuid']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        # Generate title if not provided
        if not self.title:
            self.title = f"{self.subject}: {self.topic}"
        
        # Generate share token if shared
        if self.is_shared and not self.share_token:
            self.share_token = str(uuid.uuid4())
            self.shared_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def share_url(self):
        """Get public share URL"""
        if self.share_token:
            # This would be the full URL in production
            return f"/share/{self.share_token}/"
        return None


class UsageLog(models.Model):
    """Track API usage and costs"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='usage_logs')
    lesson_plan = models.ForeignKey(LessonPlan, on_delete=models.CASCADE, null=True, blank=True, related_name='usage_logs')
    
    # API usage
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    
    # Cost tracking (in USD)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Response time
    response_time = models.FloatField(default=0, help_text="Response time in seconds")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'usage_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.total_tokens} tokens"


class SharedLessonPlanView(models.Model):
    """Track views of shared lesson plans"""
    
    lesson_plan = models.ForeignKey(LessonPlan, on_delete=models.CASCADE, related_name='views')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'shared_lesson_plan_views'
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['lesson_plan', 'viewed_at']),
        ]
    
    def __str__(self):
        return f"{self.lesson_plan.title} - {self.ip_address}"


class Feedback(models.Model):
    """User feedback on generated lesson plans"""
    
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feedbacks')
    lesson_plan = models.ForeignKey(LessonPlan, on_delete=models.CASCADE, related_name='feedbacks')
    
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    
    # What was good/bad
    quality_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    relevance_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    structure_rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feedback'
        ordering = ['-created_at']
        unique_together = ['user', 'lesson_plan']
    
    def __str__(self):
        return f"{self.user.email} - {self.rating}/5"
