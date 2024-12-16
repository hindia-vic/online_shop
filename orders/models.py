from django.db import models
from products.models import Product

class Order(models.Model):
    full_name=models.CharField(max_length=200)
    email=models.EmailField()
    address=models.CharField(max_length=250)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    paid=models.BooleanField(default=False)

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())
    
    def mark_as_paid(self):
        """Mark the order as paid."""
        self.paid = True
        self.save()

class Orderitem(models.Model):
    order=models.ForeignKey(Order,related_name='items', on_delete=models.CASCADE)
    product=models.ForeignKey(Product,related_name='order_item',on_delete=models.CASCADE)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    quantity=models.IntegerField(default=1)

    def get_cost(self):
        return self.quantity*self.price
    
    
