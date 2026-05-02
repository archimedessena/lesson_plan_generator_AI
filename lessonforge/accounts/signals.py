"""
Signal handlers for accounts app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import User, Subscription
import logging

logger = logging.getLogger('lessonforge')


@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    """Handle actions after user is created"""
    if created:
        logger.info(f"New user registered: {instance.email}")
        
        # Create free trial subscription
        Subscription.objects.create(
            user=instance,
            plan='free',
            status='active',
            end_date=timezone.now() + timedelta(days=365)  # Free plan for 1 year
        )
        
        # Additional actions:
        # - Send welcome email
        # - Create onboarding tasks
        # - Log to analytics


@receiver(post_save, sender=Subscription)
def subscription_updated(sender, instance, created, **kwargs):
    """Handle subscription updates"""
    if created:
        logger.info(f"New subscription created: {instance.user.email} - {instance.plan}")
    else:
        logger.info(f"Subscription updated: {instance.user.email} - {instance.status}")
