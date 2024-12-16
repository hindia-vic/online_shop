from django.shortcuts import render,get_object_or_404
from . models import Product,Category

def product_list(request,category_slug=None):
    category=None
    products=Product.objects.filter(available=True)
    categories=Category.objects.all()
    if category_slug:
        category=get_object_or_404(Category,slug=category_slug)
        products=products.filter(category=category)
    context={'products':products,'categories':categories,'category':category}
    return render(request,'product/product.html',context)

def product_detail(request,slug,id):
    product=get_object_or_404(Product,id=id,slug=slug,available=True)
    context={'product':product}
    return render(request,'product/detail.html',context)

# Create your views here.
