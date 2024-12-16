from django.db import models
from django.urls import reverse

# Create your models here.
class Category(models.Model):
    name=models.CharField(max_length=100)
    slug=models.SlugField(unique=True)

    def __str__(self):
       return self.name


class Product(models.Model):
    name=models.CharField(max_length=100)
    category=models.ForeignKey(Category,related_name='products', on_delete=models.CASCADE)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    description=models.TextField()
    slug=models.SlugField()
    available=models.BooleanField(default=False)
    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)
    image=models.ImageField(upload_to='products')
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products')