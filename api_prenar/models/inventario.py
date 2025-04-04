from django.db import models
from .producto import Producto
from .pedido import Pedido

class Inventario(models.Model):
    id=models.AutoField(primary_key=True)
    inventory_date=models.DateField()
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='inventarios')
    id_pedido= models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='inventarios')
    number_upload=models.CharField(max_length=255,null=True, blank=True)
    conformal_production = models.IntegerField(default=0)
    not_comformal_production = models.IntegerField(default=0)
    comformal_output = models.IntegerField(default=0)
    not_comformal_output = models.IntegerField(default=0)
    total_production = models.IntegerField(default=0)
    total_output = models.IntegerField(default=0)
    saldo_almacen = models.IntegerField() 
    cargo_number=models.CharField(null=True, blank=True, max_length=255) 
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)


