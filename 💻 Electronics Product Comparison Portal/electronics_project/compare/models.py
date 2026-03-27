# Create your models here.
from django.db import models

class Brand(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Product(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    price = models.FloatField()
    ram = models.CharField(max_length=50)
    storage = models.CharField(max_length=50)
    camera = models.CharField(max_length=50)
    battery = models.CharField(max_length=50)
    image = models.ImageField(upload_to='electronics/')

    def __str__(self):
        return self.name