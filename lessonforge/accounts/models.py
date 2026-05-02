"""
Accounts models - Custom User and Subscription
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    """Custom user model with additional fields"""
    
    CURRICULUM_CHOICES = [
        ('IGCSE', 'Cambridge IGCSE'),
        ('A_LEVEL', 'Cambridge A-Level'),
        ('WASSCE', 'WASSCE'),
        ('MULTIPLE', 'Multiple Curricula'),
    ]
    
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    school_name = models.CharField(max_length=255, blank=True)
    subjects_taught = models.TextField(blank=True, help_text="Comma-separated list")
    curriculum = models.CharField(max_length=20, choices=CURRICULUM_CHOICES, default='IGCSE')
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    # Preferences
    preferred_duration = models.IntegerField(default=60, help_text="Default lesson duration in minutes")
    preferred_grade_level = models.CharField(max_length=50, blank=True)
    
    # Metadata
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return self.full_name or self.username
    
    @property
    def has_active_subscription(self):
        """Check if user has an active paid subscription"""
        return self.subscriptions.filter(
            status='active',
            end_date__gt=timezone.now()
        ).exists()
    
    @property
    def current_subscription(self):
        """Get user's current active subscription"""
        return self.subscriptions.filter(
            status='active',
            end_date__gt=timezone.now()
        ).first()
    
    @property
    def subscription_tier(self):
        """Get current subscription tier"""
        subscription = self.current_subscription
        return subscription.plan if subscription else 'free'
    
    @property
    def monthly_limit(self):
        """Get monthly lesson plan generation limit"""
        from django.conf import settings
        subscription = self.current_subscription
        
        if not subscription:
            return settings.LESSONFORGE_FREE_PLAN_LIMIT
        
        if subscription.plan == 'teacher':
            return settings.LESSONFORGE_TEACHER_PLAN_LIMIT
        elif subscription.plan == 'school':
            return 999999  # Unlimited
        
        return settings.LESSONFORGE_FREE_PLAN_LIMIT
    
    def can_generate_lesson_plan(self):
        """Check if user can generate a new lesson plan this month"""
        from generator.models import LessonPlan
        
        # Get start of current month
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Count lesson plans generated this month
        count = LessonPlan.objects.filter(
            user=self,
            created_at__gte=month_start
        ).count()
        
        return count < self.monthly_limit


class Subscription(models.Model):
    """User subscription model"""
    
    PLAN_CHOICES = [
        ('free', 'Free Plan'),
        ('teacher', 'Teacher Plan'),
        ('school', 'School Plan'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('pending', 'Pending'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Paystack integration
    paystack_reference = models.CharField(max_length=100, unique=True, null=True, blank=True)
    paystack_subscription_code = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Dates
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['paystack_reference']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.plan} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Set end_date if not set
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=30)
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status == 'active' and self.end_date > timezone.now()
    
    @property
    def days_remaining(self):
        """Calculate days remaining in subscription"""
        if self.end_date > timezone.now():
            return (self.end_date - timezone.now()).days
        return 0


class PaymentTransaction(models.Model):
    """Track all payment transactions"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('abandoned', 'Abandoned'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Paystack data
    paystack_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - GHS {self.amount} ({self.status})"


class EmailVerificationToken(models.Model):
    """Email verification tokens"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'email_verification_tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.token}"
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)
    
    @property
    def is_valid(self):
        """Check if token is still valid"""
        return not self.used and self.expires_at > timezone.now()
