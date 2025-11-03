from django import forms
from .models import EvaluationResponse
from .models import Section
from django.contrib.auth.models import User

class CreateNewRating(forms.Form):
    name = forms.CharField(label= 'Name', max_length = 200)

class EvaluationResponseForm(forms.ModelForm):
    class Meta:
        model = EvaluationResponse
        fields = ['question1', 'question2', 'question3', 'question4', 'question5']  # Add other fields as necessary

    # You can also manually set the required fields if needed, but by default, ModelForm will enforce the model's constraints
    question1 = forms.CharField(required=True)
    question2 = forms.CharField(required=True)
    question3 = forms.CharField(required=True)
    question4 = forms.CharField(required=True)
    question5 = forms.CharField(required=True)

class UserUpdateForm(forms.ModelForm):
    password = forms.CharField(required=False, widget=forms.PasswordInput)
    section = forms.ModelChoiceField(
        queryset=Section.objects.all(),
        required=False,
        empty_label="-- Select Section --"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
