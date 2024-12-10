from django.db import models
from api_prenar.models import Pedido
from api_prenar.options.option import OPTIONS_DISPATCH_STATE

class Despacho(models.Model):
    id=models.AutoField(primary_key=True)
    id_pedido=models.OneToOneField(Pedido, on_delete=models.CASCADE)
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
