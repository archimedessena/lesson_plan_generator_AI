from django.db import models


# Create your models here.
class LessonPlan(models.Model):
    name_of_teacher = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=100)
    grade_level = models.CharField(max_length=50)
    term = models.CharField(max_length=20)
    objectives = models.TextField()
    resources = models.TextField()
    activities = models.TextField()
    assessment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title