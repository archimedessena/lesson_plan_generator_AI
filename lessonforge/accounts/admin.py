"""
Admin configuration for accounts app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Subscription, PaymentTransaction, EmailVerificationToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'full_name', 'school_name', 'curriculum', 'email_verified', 'is_staff', 'created_at']
    list_filter = ['curriculum', 'email_verified', 'is_staff', 'is_active', 'created_at']
    search_fields = ['email', 'username', 'full_name', 'school_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone', 'profile_picture')}),
        ('Professional Info', {'fields': ('school_name', 'subjects_taught', 'curriculum')}),
        ('Preferences', {'fields': ('preferred_duration', 'preferred_grade_level')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('email_verified', 'last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'start_date', 'end_date', 'days_remaining']
    list_filter = ['plan', 'status', 'created_at']
    search_fields = ['user__email', 'user__full_name', 'paystack_reference']
    date_hierarchy = 'created_at'
    
    def days_remaining(self, obj):
        return obj.days_remaining
    days_remaining.short_description = 'Days Left'


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['reference', 'user', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['reference', 'user__email']
    date_hierarchy = 'created_at'
    readonly_fields = ['paystack_data']


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'expires_at', 'used']
    list_filter = ['used', 'created_at']
    search_fields = ['user__email', 'token']
    date_hierarchy = 'created_at'
