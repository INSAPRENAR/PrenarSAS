from django.db import models
from api_prenar.models import Material, Producto

class ConsumoMaterial(models.Model):
    id=models.AutoField(primary_key=True)
    consumption_date=models.DateField()
    id_material=models.OneToOneField(Material, on_delete=models.CASCADE)
    id_producto=models.OneToOneField(Producto, on_delete=models.CASCADE)
    quantity_produced=models.IntegerField()
    base_quantity_used=models.FloatField(null=True, blank=True)
    quantity_mortar_used=models.FloatField(null=True, blank=True)
    unit_x_bult=models.FloatField(null=True, blank=True)
    unit_x_kilos=models.FloatField(null=True, blank=True)
    base_reference_unit=models.FloatField(null=True, blank=True)
    mortar_reference_unit=models.FloatField(null=True, blank=True)
    base_deviation=models.FloatField(null=True, blank=True)
    morter_deviation=models.FloatField(null=True, blank=True)
    color=models.CharField(max_length=255, null=True, blank=True)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)
