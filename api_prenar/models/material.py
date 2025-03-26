from django.db import models
from api_prenar.models.categoria_material import CategoriaMaterial
from api_prenar.options.option import OPTIONS_MATERIAL, OPTIONS_MATERIAL_MEDIDA

class Material(models.Model):
    id=models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey(CategoriaMaterial, on_delete=models.CASCADE, related_name='materiales')
    description=models.CharField(max_length=255, null=True, blank=True)
    supplier=models.CharField(max_length=255, null=True, blank=True)
    unit_price=models.FloatField()
    date_received=models.DateField(null=True, blank=True)
    amount=models.FloatField()
    extent=models.IntegerField(choices=OPTIONS_MATERIAL_MEDIDA)
    total=models.FloatField(null=True, blank=True)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)



