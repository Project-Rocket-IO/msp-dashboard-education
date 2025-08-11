from django import forms
from . models import ThreadModel, MessageModel

class ThreadModelForm(forms.ModelForm):
    class Meta:
        model = ThreadModel
        fields = '__all__'

class MessageModelForm(forms.ModelForm):
    class Meta:
        model = MessageModel
        fields = '__all__'