from django.contrib import admin
from .models import Order,Orderitem

class OrderItemInline(admin.TabularInline):
    model=Orderitem
    raw_id_fields=['product']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display=['id','full_name','email']
    inlines=[OrderItemInline]
    

