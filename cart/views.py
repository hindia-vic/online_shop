from django.shortcuts import render,get_object_or_404,redirect
from products.models import Product
from . models import CartItem,Cart
from django.http import JsonResponse
# Create your views here.

def cart_item(request,product_id):
    cart_id=request.session.get('cart_id')

    if cart_id:
        try:
            cart=Cart.objects.get(id=cart_id)

        except:
            cart=Cart.objects.create()
    else:
        cart=Cart.objects.create()
        request.session['cart_id']=cart.id

    product=get_object_or_404(Product,id=product_id)
    cart_item,created=CartItem.objects.get_or_create(cart=cart,product=product)
    if not created:
        cart_item.quantity +=1
    cart_item.save()
    response_data={
        'success':True,
        'message':f"Added {product.name} to the cart"
    }
    return  JsonResponse(response_data)
    
def cart_detail(request):
    cart_id=request.session.get('cart_id')
    cart=None
    if cart_id:
        cart=get_object_or_404(Cart,id=cart_id)
    if not cart or not  cart.items.exists():
        cart=None


    return render(request,'product/cart.html',{'cart':cart})
def cart_remove(request,product_id):
    cart_id=request.session.get('cart_id')
    cart=get_object_or_404(Cart,id=cart_id)
    item=get_object_or_404(CartItem,id=product_id,cart=cart)
    item.delete()
    return redirect('cart_detail')

