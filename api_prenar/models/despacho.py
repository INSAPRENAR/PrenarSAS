from django.db import models
from api_prenar.models import Pedido, Producto
from api_prenar.options.option import OPTIONS_DISPATCH_STATE

class Despacho(models.Model):
    id=models.AutoField(primary_key=True)
    cargo_number=models.CharField(unique=True, max_length=8)
    id_pedido=models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='despachos')
    products=models.JSONField()
    dispatch_date=models.DateField()
    driver=models.CharField(max_length=255)
    driver_identification=models.CharField(max_length=15)
    plate=models.CharField(max_length=255)
    vehicle_type=models.CharField(max_length=255)
    phone=models.CharField(max_length=255)
    dispatcher=models.CharField(max_length=255)
    warehouseman=models.CharField(max_length=255)
    entry_time=models.CharField(max_length=255)
    departure_time=models.CharField(max_length=255)
    production_number=models.CharField(max_length=255,null=True, blank=True)
    observation=models.CharField(max_length=255,null=True, blank=True)
    dispatcher_state=models.IntegerField(choices=OPTIONS_DISPATCH_STATE, default=1)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)
