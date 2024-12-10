from django.db import models
from api_prenar.models import Pedido

class Inventario(models.Model):
    id=models.AutoField(primary_key=True)
    inventory_date=models.DateField()
    id_pedido=models.OneToOneField(Pedido, on_delete=models.CASCADE)
    number_upload=models.CharField()
    conformal_production=models.IntegerField()
    not_comformal_production=models.IntegerField()
    comformal_output=models.IntegerField()
    not_comformal_output=models.IntegerField()
    total_production=models.IntegerField()
    total_output=models.IntegerField()
    balance=models.IntegerField()
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)


