from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    user =models.ForeignKey(User,on_delete=models.CASCADE)
    phone=models.IntegerField()
    name=models.CharField(max_length=250)
    address=models.CharField(max_length=100)
    def __str__(self):
        return self.

# Create your models here.
