from django.contrib.auth.models import User
from django import forms
from .models import PictureModel


FILE_CHOICES = (
        ('pdf', 'PDF'),
        ('png', 'PNG'),
        ('jpg', 'JPG'),
        ('jpeg', 'JPEG')
    )

class UserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['username', 'password']


class UploadForm(forms.Form):
    picture = forms.FileField()


class AnalyseForm(forms.Form):
    dname = forms.CharField()
    dnum = forms.CharField()

class DownloadForm(forms.Form):
    file_format  = forms.ChoiceField(choices=FILE_CHOICES, initial='PDF')
    file_name = forms.CharField(initial="Insurance permit")
