from django.db import models
from .producto import Producto
from .pedido import Pedido
from api_prenar.options.option import INVENTORY_TYPE, CATEGORIE

class Inventario(models.Model):
    id=models.AutoField(primary_key=True)
    inventory_date=models.DateField()
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='inventarios')
    id_pedido= models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='inventarios', null=True, blank=True)
    production = models.IntegerField(default=0)
    output = models.IntegerField(default=0)
    saldo_almacen = models.IntegerField() 
    cargo_number=models.CharField(null=True, blank=True, max_length=255) 
    observation=models.CharField(null=True, blank=True, max_length=255)
    inventory_type=models.IntegerField(choices=INVENTORY_TYPE, default=1)
    categori=models.IntegerField(choices=CATEGORIE, default=1)
    lote=models.CharField(null=True, blank=True, max_length=255)
    production_order=models.CharField(null=True, blank=True, max_length=255)
    transporter_name=models.CharField(null=True, blank=True, max_length=255)
    label_number_estiva=models.CharField(null=True, blank=True, max_length=255)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)


