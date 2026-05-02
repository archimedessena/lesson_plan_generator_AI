from django import forms
from .models import LessonPlan


class LessonPlanForm(forms.ModelForm):
    class Meta:
        model = LessonPlan
        fields = [
            'name_of_teacher',
            'title',
            'subject',
            'grade_level',
            'term',
            'objectives',
            'resources',
            'activities',
            'assessment'
        ]
        widgets = {
            'objectives': forms.Textarea(attrs={'rows': 4}),
            'resources': forms.Textarea(attrs={'rows': 4}),
            'activities': forms.Textarea(attrs={'rows': 4}),
            'assessment': forms.Textarea(attrs={'rows': 4}),
        }


