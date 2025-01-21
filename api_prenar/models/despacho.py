from django.db import models
from api_prenar.models import Pedido, Producto
from api_prenar.options.option import OPTIONS_DISPATCH_STATE

class Despacho(models.Model):
    id=models.AutoField(primary_key=True)
    cargo_number=models.CharField(unique=True)
    id_pedido=models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='despachos')
    id_producto=models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='despachos')
    dispatch_date=models.DateField()
    conveyor=models.CharField()
    plate=models.CharField()
    dispatcher=models.CharField()
    amount=models.IntegerField()
    dispatch_time=models.TimeField()
    destination=models.CharField()
    dispatcher_state=models.IntegerField(choices=OPTIONS_DISPATCH_STATE, default=1)
    billing_date=models.DateField(null=True, blank=True)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)
