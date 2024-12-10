from django.db import models

class Producto(models.Model):
    id=models.AutoField(primary_key=True)
    product_code=models.CharField(unique=True)
    name=models.CharField(max_length=255)
    description=models.CharField(max_length=255)
    unit_price=models.FloatField()
    color=models.CharField(max_length=255)
    warehouse_quantity=models.IntegerField()