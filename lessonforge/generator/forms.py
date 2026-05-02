"""
Forms for LessonForge application
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from accounts.models import User
from generator.models import LessonPlan, Feedback


class UserRegistrationForm(UserCreationForm):
    """User registration form with additional fields"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
    )
    
    full_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Full Name'
        })
    )
    
    school_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your School (Optional)'
        })
    )
    
    curriculum = forms.ChoiceField(
        choices=User.CURRICULUM_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    subjects_taught = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Mathematics, Physics, Chemistry'
        }),
        help_text='Comma-separated list of subjects you teach'
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+233 XX XXX XXXX'
        })
    )
    
    class Meta:
        model = User
        fields = ['email', 'username', 'full_name', 'school_name', 
                 'curriculum', 'subjects_taught', 'phone', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password (min. 8 characters)'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered.')
        return email


class UserLoginForm(AuthenticationForm):
    """Custom login form"""
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email or Username',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class LessonPlanGenerationForm(forms.Form):
    """Form for generating lesson plans"""
    
    subject = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Mathematics, Chemistry, English Literature'
        })
    )
    
    topic = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Quadratic Equations, Photosynthesis, Poetry Analysis'
        })
    )
    
    grade_level = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Year 9, Form 3, Grade 11'
        })
    )
    
    curriculum = forms.ChoiceField(
        choices=LessonPlan.CURRICULUM_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    duration = forms.IntegerField(
        min_value=30,
        max_value=180,
        initial=60,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '60'
        }),
        help_text='Duration in minutes (30-180)'
    )
    
    learning_objectives = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'List the specific learning objectives for this lesson...\n\nExample:\n- Students will be able to solve quadratic equations using the formula\n- Students will understand the discriminant and its meaning'
        }),
        help_text='Enter clear, measurable learning objectives'
    )
    
    additional_requirements = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any special requirements, focus areas, or constraints...\n\nExample:\n- Include practical examples relevant to Ghana\n- Focus on exam preparation\n- Limited resources available'
        }),
        help_text='Optional: Any additional context or requirements'
    )
    
    template = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        help_text='Optional: Choose a template structure'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Populate template choices
        from generator.models import Template
        templates = Template.objects.filter(is_public=True)
        
        # Filter premium templates if user doesn't have subscription
        if user and not user.has_active_subscription:
            templates = templates.filter(is_premium=False)
        
        template_choices = [('', '--- No Template (Default) ---')]
        template_choices.extend([
            (str(t.id), f"{t.name} ({t.get_curriculum_display()})") 
            for t in templates
        ])
        self.fields['template'].choices = template_choices
        
        # Pre-fill user preferences if available
        if user:
            self.fields['curriculum'].initial = user.curriculum
            self.fields['duration'].initial = user.preferred_duration
            if user.preferred_grade_level:
                self.fields['grade_level'].initial = user.preferred_grade_level


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    
    class Meta:
        model = User
        fields = ['full_name', 'school_name', 'subjects_taught', 'curriculum',
                 'phone', 'preferred_duration', 'preferred_grade_level', 'profile_picture']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'school_name': forms.TextInput(attrs={'class': 'form-control'}),
            'subjects_taught': forms.TextInput(attrs={'class': 'form-control'}),
            'curriculum': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'preferred_duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'preferred_grade_level': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }


class FeedbackForm(forms.ModelForm):
    """Form for submitting feedback on lesson plans"""
    
    class Meta:
        model = Feedback
        fields = ['rating', 'quality_rating', 'relevance_rating', 'structure_rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=Feedback.RATING_CHOICES),
            'quality_rating': forms.RadioSelect(choices=Feedback.RATING_CHOICES),
            'relevance_rating': forms.RadioSelect(choices=Feedback.RATING_CHOICES),
            'structure_rating': forms.RadioSelect(choices=Feedback.RATING_CHOICES),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your thoughts on this lesson plan...'
            }),
        }
