from django.db import models
from api_prenar.models import Pedido
from api_prenar.options.option import OPTIONS_PAYMENT_METHOD

class Pago(models.Model):
    id=models.AutoField(primary_key=True)
    id_pedido=models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='pagos')
    receipt_number=models.CharField(unique=True,max_length=255)
    payment_date=models.DateField()
    amount=models.FloatField()
    payment_method=models.IntegerField(choices=OPTIONS_PAYMENT_METHOD)
    observation=models.CharField(max_length=255, null=True, blank=True)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)