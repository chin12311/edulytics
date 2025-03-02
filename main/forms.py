from django import forms

class CreateNewRating(forms.Form):
    name = forms.CharField(label= 'Name', max_length = 200)