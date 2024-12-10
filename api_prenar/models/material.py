from django.db import models

class Material(models.Model):
    id=models.AutoField(primary_key=True)
    name=models.CharField(max_length=255)
    description=models.CharField(max_length=255)
    supplier=models.CharField(max_length=255)
    stock_quantity=models.IntegerField()
    unit_price=models.FloatField()
    date_received=models.DateField()
    income_amount=models.IntegerField()
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)


