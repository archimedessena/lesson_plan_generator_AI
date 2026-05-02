"""
Views for accounts app - authentication and profile management
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid
import logging

from .models import User, Subscription, EmailVerificationToken, PaymentTransaction
from generator.forms import ProfileUpdateForm, UserRegistrationForm, UserLoginForm

logger = logging.getLogger('lessonforge')


def register(request):
    """User registration view"""
    
    if request.user.is_authenticated:
        return redirect('generator:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            
            # Create verification token (optional)
            token = str(uuid.uuid4())
            EmailVerificationToken.objects.create(
                user=user,
                token=token
            )
            
            # Send verification email would go here
            # For now, just auto-verify in development
            if settings.DEBUG:
                user.email_verified = True
                user.save(update_fields=['email_verified'])
            
            # Log the user in
            login(request, user)
            
            messages.success(request, 'Account created successfully! Welcome to LessonForge.')
            return redirect('generator:dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    """User login view"""
    
    if request.user.is_authenticated:
        return redirect('generator:dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Try to authenticate with email first
            user = None
            if '@' in username:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            # Try with username if email didn't work
            if not user:
                user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                
                # Redirect to next page or dashboard
                next_url = request.GET.get('next', 'generator:dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid email/username or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('generator:home')


@login_required
def profile(request):
    """User profile view"""
    
    # Get subscription info
    subscription = request.user.current_subscription
    
    # Get usage statistics
    total_plans = request.user.lesson_plans.count()
    
    # Monthly usage
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_usage = request.user.lesson_plans.filter(created_at__gte=month_start).count()
    
    context = {
        'subscription': subscription,
        'total_plans': total_plans,
        'monthly_usage': monthly_usage,
        'monthly_limit': request.user.monthly_limit,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    """Edit user profile"""
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def subscription_management(request):
    """Manage subscription"""
    
    current_subscription = request.user.current_subscription
    all_subscriptions = request.user.subscriptions.all()[:10]
    
    context = {
        'current_subscription': current_subscription,
        'all_subscriptions': all_subscriptions,
    }
    
    return render(request, 'accounts/subscription.html', context)


@login_required
def initiate_payment(request, plan):
    """Initiate payment for a subscription plan"""
    
    if plan not in ['teacher', 'school']:
        messages.error(request, 'Invalid plan selected.')
        return redirect('generator:pricing')
    
    # Get plan price
    if plan == 'teacher':
        amount = settings.LESSONFORGE_TEACHER_PLAN_PRICE
    else:
        amount = settings.LESSONFORGE_SCHOOL_PLAN_PRICE
    
    # Create payment transaction
    reference = f"LF-{uuid.uuid4().hex[:12].upper()}"
    
    transaction = PaymentTransaction.objects.create(
        user=request.user,
        reference=reference,
        amount=amount / 100,  # Convert from pesewas to cedis
        status='pending'
    )
    
    # In production, integrate with Paystack
    # For now, show a payment page
    context = {
        'plan': plan,
        'amount': amount / 100,
        'reference': reference,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
    }
    
    return render(request, 'accounts/payment.html', context)


@login_required
def verify_payment(request):
    """Verify payment after Paystack redirect"""
    
    reference = request.GET.get('reference')
    
    if not reference:
        messages.error(request, 'Invalid payment reference.')
        return redirect('generator:pricing')
    
    try:
        transaction = PaymentTransaction.objects.get(
            reference=reference,
            user=request.user
        )
        
        # In production, verify with Paystack API
        # For now, just mark as successful in development
        if settings.DEBUG:
            transaction.status = 'success'
            transaction.save()
            
            # Determine plan from amount
            if transaction.amount == settings.LESSONFORGE_TEACHER_PLAN_PRICE / 100:
                plan = 'teacher'
            else:
                plan = 'school'
            
            # Create subscription
            end_date = timezone.now() + timedelta(days=30)
            subscription = Subscription.objects.create(
                user=request.user,
                plan=plan,
                status='active',
                paystack_reference=reference,
                end_date=end_date
            )
            
            transaction.subscription = subscription
            transaction.save()
            
            messages.success(request, f'Payment successful! Your {plan.title()} Plan is now active.')
            return redirect('accounts:subscription')
        
        messages.info(request, 'Payment verification in progress...')
        return redirect('accounts:subscription')
        
    except PaymentTransaction.DoesNotExist:
        messages.error(request, 'Payment transaction not found.')
        return redirect('generator:pricing')


@login_required
def cancel_subscription(request):
    """Cancel active subscription"""
    
    subscription = request.user.current_subscription
    
    if not subscription:
        messages.error(request, 'No active subscription to cancel.')
        return redirect('accounts:subscription')
    
    if request.method == 'POST':
        subscription.status = 'cancelled'
        subscription.cancelled_at = timezone.now()
        subscription.save()
        
        messages.success(request, 'Subscription cancelled. You can continue using premium features until the end of your billing period.')
        return redirect('accounts:subscription')
    
    return render(request, 'accounts/cancel_subscription.html', {'subscription': subscription})


def verify_email(request, token):
    """Verify email address"""
    
    try:
        verification = EmailVerificationToken.objects.get(token=token, used=False)
        
        if verification.is_valid:
            verification.user.email_verified = True
            verification.user.save(update_fields=['email_verified'])
            
            verification.used = True
            verification.save()
            
            messages.success(request, 'Email verified successfully! You can now log in.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'This verification link has expired.')
            return redirect('generator:home')
            
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('generator:home')
