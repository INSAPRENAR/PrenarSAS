from django.db import models

class Producto(models.Model):
    id=models.AutoField(primary_key=True)
    product_code=models.CharField(unique=True)
    name=models.CharField(max_length=255)
    description=models.CharField(max_length=255, null=True, blank=True)
    unit_price=models.FloatField()
    discounted_unit_price=models.FloatField()
    color=models.CharField(max_length=255)
    warehouse_quantity=models.IntegerField()
    weight=models.FloatField(null=True, blank=True)
    quantity_x_m2=models.FloatField(null=True, blank=True)
    price_x_meter=models.FloatField(null=True, blank=True)
    inches=models.FloatField(null=True, blank=True)
    millimeters=models.FloatField(null=True, blank=True)
    production_x_day=models.IntegerField(null=True, blank=True)
    production_x_month=models.IntegerField(null=True, blank=True)
    quantity_x_estiva=models.IntegerField(null=True, blank=True)