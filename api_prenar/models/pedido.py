from django.db import models
from api_prenar.models import Cliente
from api_prenar.options.option import OPTIONS_COMPANY

class Pedido(models.Model):
    id=models.AutoField(primary_key=True)
    id_client=models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pedidos')
    order_code=models.CharField(unique=True,max_length=255)
    order_date=models.DateField()
    delivery_date=models.DateField()
    address=models.CharField(max_length=255, null=True, blank=True)
    phone=models.CharField(max_length=15, null=True, blank=True)
    total=models.FloatField(default=0.0)
    total_discount_ordered=models.IntegerField(default=0,null=True, blank=True)
    state=models.IntegerField()
    outstanding_balance=models.FloatField(default=0.0)
    products=models.JSONField()
    company=models.IntegerField(choices=OPTIONS_COMPANY)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)
    #cantidad=models.IntegerField() ver si ó no

    def save(self, *args, **kwargs):
        # Solo inicializa el saldo pendiente si es None (no ha sido asignado)
        if self.outstanding_balance is None:
            self.outstanding_balance = self.total
        super().save(*args, **kwargs)

