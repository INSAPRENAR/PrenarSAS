from django.db import models
from api_prenar.models import Pedido, Producto
from api_prenar.options.option import OPTIONS_CALENDARIO_STATE, OPTIONS_CALENDARIO_MACHINE

class Calendario(models.Model):
    id=models.AutoField(primary_key=True)
    calendar_date=models.DateField()
    type=models.IntegerField()
    expected_date=models.DateField()
    id_pedido=models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='calendarios')
    amount=models.IntegerField()
    id_producto=models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='calendarios')
    dispatch_time=models.CharField(max_length=255, null=True, blank=True)
    machine=models.IntegerField(choices=OPTIONS_CALENDARIO_MACHINE, null=True, blank=True)
    state=models.IntegerField(default=2, choices=OPTIONS_CALENDARIO_STATE)
    observation=models.CharField(max_length=255, null=True, blank=True)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)