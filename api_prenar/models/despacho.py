from django.db import models
from api_prenar.models import Pedido, Producto
from api_prenar.options.option import OPTIONS_DISPATCH_STATE

class Despacho(models.Model):
    id=models.AutoField(primary_key=True)
    cargo_number=models.CharField(unique=True, max_length=8)
    id_pedido=models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='despachos')
    products=models.JSONField()
    dispatch_date=models.DateField()
    driver=models.CharField()
    driver_identification=models.CharField(max_length=15)
    plate=models.CharField()
    vehicle_type=models.CharField()
    phone=models.CharField()
    dispatcher=models.CharField()
    warehouseman=models.CharField()
    entry_time=models.CharField()
    departure_time=models.CharField()
    rotulo_number=models.CharField()
    production_number=models.CharField()
    observation=models.CharField()
    dispatcher_state=models.IntegerField(choices=OPTIONS_DISPATCH_STATE, default=1)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)
