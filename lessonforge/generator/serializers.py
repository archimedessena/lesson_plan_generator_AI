"""
REST API Serializers for generator app
"""
from rest_framework import serializers
from .models import LessonPlan, Template, Feedback


class TemplateSerializer(serializers.ModelSerializer):
    """Serializer for Template model"""
    
    class Meta:
        model = Template
        fields = ['id', 'name', 'slug', 'description', 'curriculum', 'subject', 
                 'is_public', 'is_premium', 'usage_count', 'created_at']
        read_only_fields = ['id', 'slug', 'usage_count', 'created_at']


class LessonPlanListSerializer(serializers.ModelSerializer):
    """Serializer for listing lesson plans"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    curriculum_display = serializers.CharField(source='get_curriculum_display', read_only=True)
    pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = LessonPlan
        fields = ['uuid', 'title', 'subject', 'topic', 'grade_level', 'curriculum', 
                 'curriculum_display', 'duration', 'user_email', 'is_favorite', 
                 'pdf_url', 'created_at']
        read_only_fields = ['uuid', 'created_at']
    
    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
        return None


class LessonPlanDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed lesson plan view"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    curriculum_display = serializers.CharField(source='get_curriculum_display', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True, allow_null=True)
    pdf_url = serializers.SerializerMethodField()
    share_url = serializers.SerializerMethodField()
    
    class Meta:
        model = LessonPlan
        fields = ['uuid', 'title', 'subject', 'topic', 'grade_level', 'curriculum', 
                 'curriculum_display', 'duration', 'learning_objectives', 
                 'additional_requirements', 'content', 'template_name', 'user_email',
                 'is_favorite', 'is_shared', 'pdf_url', 'share_url', 'generation_time',
                 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'generation_time', 'created_at', 'updated_at']
    
    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
        return None
    
    def get_share_url(self, obj):
        if obj.share_token:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/share/{obj.share_token}/')
        return None


class LessonPlanCreateSerializer(serializers.Serializer):
    """Serializer for creating lesson plans"""
    
    subject = serializers.CharField(max_length=100)
    topic = serializers.CharField(max_length=300)
    grade_level = serializers.CharField(max_length=50)
    curriculum = serializers.ChoiceField(choices=LessonPlan.CURRICULUM_CHOICES)
    duration = serializers.IntegerField(min_value=30, max_value=180)
    learning_objectives = serializers.CharField()
    additional_requirements = serializers.CharField(required=False, allow_blank=True)
    template_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_template_id(self, value):
        if value:
            try:
                template = Template.objects.get(id=value, is_public=True)
                # Check if user has access to premium templates
                user = self.context['request'].user
                if template.is_premium and not user.has_active_subscription:
                    raise serializers.ValidationError("This template requires a paid subscription.")
                return value
            except Template.DoesNotExist:
                raise serializers.ValidationError("Template not found.")
        return value


class FeedbackSerializer(serializers.ModelSerializer):
    """Serializer for Feedback model"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    lesson_plan_title = serializers.CharField(source='lesson_plan.title', read_only=True)
    
    class Meta:
        model = Feedback
        fields = ['id', 'user_email', 'lesson_plan_title', 'rating', 
                 'quality_rating', 'relevance_rating', 'structure_rating', 
                 'comment', 'created_at']
        read_only_fields = ['id', 'user_email', 'lesson_plan_title', 'created_at']
