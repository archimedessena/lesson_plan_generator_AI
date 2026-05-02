"""
Signal handlers for generator app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LessonPlan
import logging

logger = logging.getLogger('lessonforge')


@receiver(post_save, sender=LessonPlan)
def lesson_plan_created(sender, instance, created, **kwargs):
    """Handle actions after lesson plan is created"""
    if created:
        logger.info(f"New lesson plan created: {instance.uuid} by {instance.user.email}")
        
        # Additional actions can be added here:
        # - Send email notification
        # - Update user statistics
        # - Log to analytics
