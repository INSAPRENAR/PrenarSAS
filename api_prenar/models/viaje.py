from django.db import models
from api_prenar.models import Pedido

class Viaje(models.Model):
    id=models.AutoField(primary_key=True)
    id_pedido=models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='viajes')
    date=models.DateField()
    shipping_value=models.FloatField(null=True, blank=True)
    product=models.IntegerField(null=True)
    total_product=models.IntegerField()
    invoice_fvsa=models.CharField(max_length=255, null=True, blank=True)
    sales_value=models.FloatField()
    product_value_balance=models.FloatField()
    shipping_value_balance=models.FloatField()
    shipping_value_paid=models.FloatField()
    shipping_sent=models.IntegerField(null=True, blank=True)
    returned_shipping=models.IntegerField(null=True, blank=True)
    returned_shipping_balance=models.IntegerField(null=True, blank=True)
    email_user=models.EmailField()