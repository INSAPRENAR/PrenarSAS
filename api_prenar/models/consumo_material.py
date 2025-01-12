from django.db import models
from api_prenar.models import Producto
from api_prenar.models.categoria_material import CategoriaMaterial

class ConsumoMaterial(models.Model):
    id=models.AutoField(primary_key=True)
    consumption_date=models.DateField()
    id_categoria=models.ForeignKey(CategoriaMaterial, on_delete=models.CASCADE, related_name='consumo_materiales')
    id_producto=models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='consumo_materiales')
    quantity_produced=models.IntegerField(null=True, blank=True)
    base_quantity_used=models.FloatField(null=True, blank=True)
    quantity_mortar_used=models.FloatField(null=True, blank=True)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)
