from django.db import models
from api_prenar.models import Producto
from api_prenar.models.categoria_material import CategoriaMaterial
from api_prenar.options.option import MATERIAL_CONSUMPTION_UNIT

class ConsumoMaterial(models.Model):
    id=models.AutoField(primary_key=True)
    consumption_date=models.DateField()
    id_categoria=models.ForeignKey(CategoriaMaterial, on_delete=models.CASCADE, related_name='consumo_materiales')
    id_producto=models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='consumo_materiales')
    quantity_produced=models.IntegerField(null=True, blank=True)
    base_quantity_used=models.FloatField(null=True, blank=True)
    quantity_mortar_used=models.FloatField(null=True, blank=True)
    total=models.FloatField(default=0.0)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)
    unit_X_base_package=models.FloatField(null=True, blank=True)
    estimated_base_reference_units=models.IntegerField(null=True, blank=True)
    base_variation=models.FloatField(null=True, blank=True)
    kilos_X_base_unit=models.FloatField(null=True, blank=True)
    unit_X_package_mortar=models.FloatField(null=True, blank=True)
    estimated_units_reference_mortar=models.IntegerField(null=True, blank=True)
    mortar_variation=models.FloatField(null=True, blank=True)
    kilos_X_unit_mortar=models.FloatField(null=True, blank=True)
    unit=models.IntegerField(choices=MATERIAL_CONSUMPTION_UNIT)
