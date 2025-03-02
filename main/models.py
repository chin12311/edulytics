from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Role(models.TextChoices):
    STUDENT = 'Student', 'Student'
    DEAN = 'Dean', 'Dean'
    COORDINATOR = 'Coordinator', 'Coordinator'
    FACULTY = 'Faculty', 'Faculty'
    ADMIN = 'Admin', 'Admin'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete= models.CASCADE)
    role = models.CharField(max_length=20, default= Role.STUDENT)

class Teacher(models.Model):
    # institute
    # teacher
    # section
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)

    def average_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():
            return sum(rating.score for rating in ratings)
        return 0
    
    def __str__(self):
        return self.name
    
class Rating(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='ratings')
    score = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    review = models.TextField(blank = True, null= True)
    created_at = models.DateTimeField(auto_now_add=True)


    # class Meta:
    #    unique_together = ('teacher', 'student')

    def __str__(self):
        return f'{self.teacher.name} - {self.score}'
    
class Evaluation(models.Model):
    evaluator = models.ForeignKey(User, on_delete= models.CASCADE, related_name='ratings')
    evaluated_at = models.DateTimeField(auto_now_add=True)