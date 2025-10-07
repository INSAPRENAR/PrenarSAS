from django.db import models
from api_prenar.options.option import OPTIONS_MATERIAL_MEDIDA

class CategoriaMaterial(models.Model):
    id=models.AutoField(primary_key=True)
    name=models.CharField(max_length=255)
    color=models.CharField(max_length=255, null=True, blank=True)
    stock_quantity=models.FloatField(default=0.0)
    extent=models.IntegerField(choices=OPTIONS_MATERIAL_MEDIDA)