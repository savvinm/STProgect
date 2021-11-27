from django.db import models

class Admin(models.Model):
    login = models.CharField(max_length=20)
    password = models.CharField(max_length=64)
    city = models.CharField(max_length=32)
