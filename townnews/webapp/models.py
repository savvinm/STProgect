from django.db import models

class City(models.Model):
    cityName = models.CharField(max_length=64)
    formForText = models.CharField(max_length=64)

class Admin(models.Model):
    login = models.CharField(max_length=20)
    password = models.CharField(max_length=64)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

class Resources(models.Model):
    path = models.FileField()

class NewsArticles(models.Model):
    title = models.CharField(max_length=128)
    tags = models.CharField(max_length=32)
    image = models.ForeignKey(Resources, on_delete=models.CASCADE)
    mainText = models.TextField()
    creationTime = models.DateTimeField()
    city = models.ForeignKey(City, on_delete=models.CASCADE)

class Promo(models.Model):
    title = models.CharField(max_length=128)
    image = models.ForeignKey(Resources, on_delete=models.CASCADE)
    promocode = models.CharField(max_length=64)
    creationTime = models.DateTimeField()
    expirationTime = models.DateField()
    city = models.ForeignKey(City, on_delete=models.CASCADE)
