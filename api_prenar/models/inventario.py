from django.db import models
from .producto import Producto

class Inventario(models.Model):
    id=models.AutoField(primary_key=True)
    inventory_date=models.DateField()
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='inventarios')
    number_upload=models.CharField(null=True, blank=True)
    conformal_production = models.IntegerField(default=0)
    not_comformal_production = models.IntegerField(default=0)
    comformal_output = models.IntegerField(default=0)
    not_comformal_output = models.IntegerField(default=0)
    total_production = models.IntegerField(default=0)
    total_output = models.IntegerField(default=0) 
    balance = models.IntegerField(default=0)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)


