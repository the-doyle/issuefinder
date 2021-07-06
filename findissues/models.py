from django.db import models
from django import forms

# Create your models here.

class FileFieldForm(forms.Form):

    TOPIC = (
            ('intend to resell', 'intend to resell'),
            ('pending credit transaction', 'pending credit transaction'),
            ('confidentiality restrictions', 'confidentiality restrictions'),
            ('compliance reporting', 'compliance reporting'),
            ('physiological process', 'physiological process'),
            ('export control regulation', 'export control regulations'),
            ('interbank rates', 'interbank rates'),
            ('distribution partner', 'distribution partner'), 
        )
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    topic = models.CharField(max_length=30, choices=TOPIC, null=False, blank=False)
    user_search = models.CharField(null=False, blank=False)