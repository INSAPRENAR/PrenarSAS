from django.db import models

class GeneracionPassword(models.Model):
    id=models.AutoField(primary_key=True)
    description=models.CharField(max_length=255)
    password_generation=models.CharField(max_length=8)
    