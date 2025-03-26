from django.db import models

class CategoriaMaterial(models.Model):
    id=models.AutoField(primary_key=True)
    name=models.CharField(max_length=255)
    color=models.CharField(max_length=255, null=True, blank=True)
    stock_quantity=models.FloatField(default=0.0)