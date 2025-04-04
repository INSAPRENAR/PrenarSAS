from django.db import models

class Cliente(models.Model):
    id=models.AutoField(primary_key=True)
    name=models.CharField(max_length=250)
    phone=models.CharField(max_length=15, null=True, blank=True)
    address=models.CharField(max_length=255,null=True, blank=True)
    email=models.EmailField()
    identification=models.CharField(max_length=255,unique=True)
    identification_asesor=models.CharField(max_length=255,null=True, blank=True)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)