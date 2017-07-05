from django.db import models

class PictureModel(models.Model):
    picture = models.FileField(upload_to='media', blank=True)
