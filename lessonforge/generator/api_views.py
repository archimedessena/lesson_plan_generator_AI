"""
REST API Views for generator app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile

from .models import LessonPlan, Template, Feedback
from .serializers import (
    LessonPlanListSerializer, LessonPlanDetailSerializer,
    LessonPlanCreateSerializer, TemplateSerializer, FeedbackSerializer
)
from .services import lesson_plan_generator
from .pdf_service import pdf_generator
import logging

logger = logging.getLogger('lessonforge')


class TemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for templates
    GET /api/templates/ - List all public templates
    GET /api/templates/{id}/ - Get template details
    """
    queryset = Template.objects.filter(is_public=True)
    serializer_class = TemplateSerializer
    permission_classes = []  # Public access
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by curriculum
        curriculum = self.request.query_params.get('curriculum', None)
        if curriculum:
            queryset = queryset.filter(curriculum=curriculum) | queryset.filter(curriculum='ALL')
        
        # Filter by subject
        subject = self.request.query_params.get('subject', None)
        if subject:
            queryset = queryset.filter(subject=subject) | queryset.filter(subject='GENERAL')
        
        # Hide premium templates if user not authenticated or no subscription
        if not self.request.user.is_authenticated or not self.request.user.has_active_subscription:
            queryset = queryset.filter(is_premium=False)
        
        return queryset.order_by('-usage_count', 'name')


class LessonPlanViewSet(viewsets.ModelViewSet):
    """
    API endpoint for lesson plans
    GET /api/lesson-plans/ - List user's lesson plans
    POST /api/lesson-plans/ - Create new lesson plan
    GET /api/lesson-plans/{uuid}/ - Get lesson plan details
    PUT /api/lesson-plans/{uuid}/ - Update lesson plan
    DELETE /api/lesson-plans/{uuid}/ - Delete lesson plan
    """
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'
    
    def get_queryset(self):
        return LessonPlan.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return LessonPlanListSerializer
        elif self.action == 'create':
            return LessonPlanCreateSerializer
        return LessonPlanDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new lesson plan"""
        
        # Check if user can generate
        if not request.user.can_generate_lesson_plan():
            return Response(
                {'error': 'Monthly limit reached. Please upgrade your plan.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Get template if specified
            template = None
            template_id = serializer.validated_data.get('template_id')
            if template_id:
                template = Template.objects.get(id=template_id)
            
            # Generate lesson plan
            content, metadata = lesson_plan_generator.generate_lesson_plan(
                subject=serializer.validated_data['subject'],
                topic=serializer.validated_data['topic'],
                grade_level=serializer.validated_data['grade_level'],
                curriculum=serializer.validated_data['curriculum'],
                duration=serializer.validated_data['duration'],
                objectives=serializer.validated_data['learning_objectives'],
                additional_requirements=serializer.validated_data.get('additional_requirements', ''),
                template=template
            )
            
            # Create lesson plan object
            lesson_plan = LessonPlan.objects.create(
                user=request.user,
                template=template,
                subject=serializer.validated_data['subject'],
                topic=serializer.validated_data['topic'],
                grade_level=serializer.validated_data['grade_level'],
                curriculum=serializer.validated_data['curriculum'],
                duration=serializer.validated_data['duration'],
                learning_objectives=serializer.validated_data['learning_objectives'],
                additional_requirements=serializer.validated_data.get('additional_requirements', ''),
                content=content,
                generation_time=metadata['generation_time']
            )
            
            # Generate PDF
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
            
            # Return created lesson plan
            output_serializer = LessonPlanDetailSerializer(lesson_plan, context={'request': request})
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating lesson plan: {str(e)}")
            return Response(
                {'error': f'Failed to generate lesson plan: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, uuid=None):
        """Toggle favorite status"""
        lesson_plan = self.get_object()
        lesson_plan.is_favorite = not lesson_plan.is_favorite
        lesson_plan.save(update_fields=['is_favorite'])
        
        serializer = self.get_serializer(lesson_plan)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def share(self, request, uuid=None):
        """Generate shareable link"""
        lesson_plan = self.get_object()
        
        if not lesson_plan.is_shared:
            lesson_plan.is_shared = True
            lesson_plan.save()
        
        share_url = request.build_absolute_uri(f'/share/{lesson_plan.share_token}/')
        return Response({'share_url': share_url})
    
    @action(detail=True, methods=['get'])
    def download(self, request, uuid=None):
        """Download PDF"""
        lesson_plan = self.get_object()
        
        if not lesson_plan.pdf_file:
            return Response(
                {'error': 'PDF not available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        pdf_url = request.build_absolute_uri(lesson_plan.pdf_file.url)
        return Response({'pdf_url': pdf_url})


class FeedbackViewSet(viewsets.ModelViewSet):
    """
    API endpoint for feedback
    GET /api/feedback/ - List user's feedback
    POST /api/feedback/ - Submit feedback
    """
    permission_classes = [IsAuthenticated]
    serializer_class = FeedbackSerializer
    
    def get_queryset(self):
        return Feedback.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
