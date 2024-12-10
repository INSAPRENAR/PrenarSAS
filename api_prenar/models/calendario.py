from django.db import models
from api_prenar.models import Pedido, Producto

class Calendario(models.Model):
    id=models.AutoField(primary_key=True)
    calendar_date=models.DateField()
    type=models.IntegerField()
    expected_date=models.DateField()
    id_pedido=models.OneToOneField(Pedido, on_delete=models.CASCADE)
    amount=models.IntegerField()
    id_producto=models.OneToOneField(Producto, on_delete=models.CASCADE)
    dispatch_time=models.TimeField(null=True, blank=True)
    machine=models.CharField(null=True, blank=True)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)