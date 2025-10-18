from django.db import models

class CalendarioDespacho(models.Model):
    id=models.AutoField(primary_key=True)
    start_date=models.DateField()
    end_date=models.DateField()
    dispatch=models.JSONField()
    pending_dispatch_balance=models.JSONField()
    observation=models.CharField(max_length=255, null=True, blank=True)
    email_user=models.EmailField()
    registration_date=models.DateField(auto_now_add=True)