from django.db import models
from api_prenar.models import Pedido

class EstivaDevuelta(models.Model):
    id=models.AutoField(primary_key=True)
    id_pedido=models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='estivas')
    delivery_date=models.DateField(null=True, blank=True)
    estiva_amount_returned=models.IntegerField()
    remaining_total=models.IntegerField()
    observation=models.CharField(max_length=255, null=True, blank=True)