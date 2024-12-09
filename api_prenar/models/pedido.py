from django.db import models
from api_prenar.models import Cliente
from api_prenar.options.option import OPTIONS_COMPANY

class Pedido(models.Model):
    id=models.AutoField(primary_key=True)
    id_client=models.OneToOneField(Cliente, on_delete=models.CASCADE)
    order_code=models.CharField(unique=True)
    order_date=models.DateField()
    delivery_date=models.DateField()
    address=models.CharField(max_length=255, null=True, blank=True)
    phone=models.CharField(max_length=15, null=True, blank=True)
    total=models.FloatField()
    state=models.IntegerField()
    outstanding_balance=models.FloatField()
    products=models.JSONField()
    company=models.IntegerField(choices=OPTIONS_COMPANY)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)
    #cantidad=models.IntegerField() ver si ó no

