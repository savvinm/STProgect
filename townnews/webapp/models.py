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

class Tag(models.Model):
    title = models.CharField(max_length=64)
    important = models.BooleanField()

class NewsArticles(models.Model):
    title = models.CharField(max_length=128)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
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
    
class User(models.Model):
    login = models.CharField(max_length=64)

class DeferredLinks(models.Model):
    task = models.CharField(max_length=64)
    address = models.CharField(max_length=64)
    platform = models.CharField(max_length=256)
    creationTime = models.DateTimeField()
    status = models.CharField(max_length=16)

class AppInit(models.Model):
    address = models.CharField(max_length=64)
    platform = models.CharField(max_length=32)
    lastInit = models.DateTimeField()
    uuiId = models.CharField(max_length=64)


class Favorites(models.Model):
    article = models.ForeignKey(NewsArticles, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class MissingPeople(models.Model):
    name = models.CharField(max_length=64)
    clothes = models.TextField()
    specCharacteristics = models.TextField()
    characteristics = models.TextField()
    lastLocation = models.CharField(max_length=150)
    dateOfBirth = models.DateField()
    sex = models.CharField(max_length=12)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ForeignKey(Resources, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=12)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    status = models.CharField(max_length=12)
