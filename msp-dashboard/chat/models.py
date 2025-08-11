from django.db import models
from apps import models as appmodels
from django.utils import timezone


class ThreadModel(models.Model):
  user = models.ForeignKey(appmodels.TechnicianUser, on_delete=models.CASCADE, related_name='+')
  receiver = models.ForeignKey(appmodels.TechnicianUser, on_delete=models.CASCADE, related_name='+')
  read = models.BooleanField(default=False)


class MessageModel(models.Model):
  thread = models.ForeignKey('ThreadModel', related_name='+', on_delete=models.CASCADE, blank=True, null=True)
  sender = models.ForeignKey(appmodels.TechnicianUser, on_delete=models.CASCADE, related_name='+')
  receiver = models.ForeignKey(appmodels.TechnicianUser, on_delete=models.CASCADE, related_name='+')
  body = models.CharField(max_length=1000)
  image = models.ImageField(upload_to='', blank=True, null=True)
  date = models.DateTimeField(default=timezone.now)
  read = models.BooleanField(default=False)

