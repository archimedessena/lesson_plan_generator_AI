"""
Admin configuration for generator app
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Template, LessonPlan, UsageLog, SharedLessonPlanView, Feedback


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'curriculum', 'subject', 'is_public', 'is_premium', 'usage_count', 'created_at']
    list_filter = ['curriculum', 'subject', 'is_public', 'is_premium', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'curriculum', 'subject')
        }),
        ('Template Configuration', {
            'fields': ('structure', 'system_prompt_addition')
        }),
        ('Access Control', {
            'fields': ('is_public', 'is_premium', 'created_by')
        }),
        ('Statistics', {
            'fields': ('usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LessonPlan)
class LessonPlanAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'subject', 'curriculum', 'grade_level', 'is_favorite', 'is_shared', 'created_at']
    list_filter = ['curriculum', 'is_favorite', 'is_shared', 'created_at']
    search_fields = ['title', 'topic', 'subject', 'user__email']
    readonly_fields = ['uuid', 'generation_time', 'share_token', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User', {
            'fields': ('user', 'template')
        }),
        ('Lesson Details', {
            'fields': ('title', 'subject', 'topic', 'grade_level', 'curriculum', 'duration')
        }),
        ('Input Data', {
            'fields': ('learning_objectives', 'additional_requirements')
        }),
        ('Generated Content', {
            'fields': ('content', 'pdf_file')
        }),
        ('Metadata', {
            'fields': ('uuid', 'is_favorite', 'generation_time', 'created_at', 'updated_at')
        }),
        ('Sharing', {
            'fields': ('is_shared', 'share_token', 'shared_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Lesson plans should only be created through the app
        return False


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson_plan', 'total_tokens', 'estimated_cost', 'response_time', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'lesson_plan__title']
    readonly_fields = ['user', 'lesson_plan', 'input_tokens', 'output_tokens', 'total_tokens', 
                      'estimated_cost', 'response_time', 'created_at']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SharedLessonPlanView)
class SharedLessonPlanViewAdmin(admin.ModelAdmin):
    list_display = ['lesson_plan', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['lesson_plan__title', 'ip_address']
    readonly_fields = ['lesson_plan', 'ip_address', 'user_agent', 'viewed_at']
    date_hierarchy = 'viewed_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson_plan', 'rating', 'created_at']
    list_filter = ['rating', 'quality_rating', 'relevance_rating', 'structure_rating', 'created_at']
    search_fields = ['user__email', 'lesson_plan__title', 'comment']
    readonly_fields = ['user', 'lesson_plan', 'created_at']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False
