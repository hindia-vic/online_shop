from django.shortcuts import render,redirect,get_object_or_404
from cart.models import Cart
from .forms import OrderCreateForm
from .models import Orderitem,Order
from django.conf import settings
from django.views.generic.base import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json 
import stripe
import requests
import base64
import datetime

stripe.api_key = settings.STRIPE_SECRET_KEY

def order_create(request):
    cart=None
    cart_id=request.session.get('cart_id')
    if cart_id:
        cart=Cart.objects.get(id=cart_id)

        if not cart or not cart.items.exists():
          return redirect('cart_detail')
    if request.method=='POST':
        form=OrderCreateForm(request.POST)
        if form.is_valid():
            order=form.save(commit=False)
            order.save()

            for item in cart.items.all():
                Orderitem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )
            cart.delete()
            del request.session['cart_id']
            return redirect('order_confirmation',order.id)
        else:
            form=OrderCreateForm()
        return render(request,'product/order_create.html',{'cart':cart,'form':form})
            

def order_confirmation(request,order_id):
    order=get_object_or_404(Order,id=order_id)
    return render(request,'product/order_confirmation.html',{'order':order})

class OrdersPageView(TemplateView):
 template_name = 'product/payment_confirmation.html'

 def get_context_data(self, **kwargs): # new
  context = super().get_context_data(**kwargs)
  context['stripe_key'] = settings.STRIPE_PUBLISHABLE_KEY
  order_id = self.kwargs.get('order_id')
  context['order'] = get_object_or_404(Order, id=order_id)
  return context

def charge(request, order_id):
    # Get the specific order
    order = get_object_or_404(Order, id=order_id)
    price = int(order.get_total_cost() * 100)  # Convert dollars to cents

    if request.method == 'POST':
        try:
            # Create a charge
            charge = stripe.Charge.create(
                amount=price,
                currency='usd',
                description='Order payment',
                source=request.POST['stripeToken']
            )
            # You can mark the order as paid if the charge is successful
            order.paid = True
            order.save()

            return render(request, 'product/charge.html', {'order': order})

        except stripe.error.StripeError as e:
            # Handle error if something goes wrong with the charge
            return render(request, 'product/error.html', {'error': str(e)})

    # If request is not POST, redirect or handle differently
    return redirect('order_confirmation', order_id=order_id)

def get_mpesa_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    response = requests.get(api_url, auth=(consumer_key, consumer_secret))
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        print(f"Access Token: {access_token}")
        return access_token
  
    else:
        print(f"Error Response: {response.content}")
        raise Exception('Failed to get access token')
       

def lipa_na_mpesa(phone_number, amount, account_reference, transaction_desc):
    access_token = get_mpesa_access_token()
    api_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode((settings.MPESA_SHORTCODE + settings.MPESA_PASSKEY + timestamp).encode()).decode()

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,  # Phone number initiating the payment
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://7a19-102-211-145-195.ngrok-free.app/order/callback/",  # Replace with your callback endpoint
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc,
    }

    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()
def initiate_payment(request,order_id):
    order = get_object_or_404(Order, id=order_id)
    price = int(order.get_total_cost() * 100)
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')  # Input from user
        amount =price # Input from user

        response = lipa_na_mpesa(phone_number, amount, order_id, "Payment for order")
        
        if response.get('ResponseCode') == '0':
            return JsonResponse({'message': 'Payment initiated successfully'})
        else:
            return JsonResponse({'error': response.get('errorMessage')}, status=400)
    
    return render(request, 'product/initiate_payment.html')

@csrf_exempt  # Disable CSRF validation for this view
def mpesa_callback(request):
    if request.method == 'POST':
        # Parse the incoming JSON data
        data = json.loads(request.body)
        
        # Log the data or handle it as needed
        print("M-Pesa Callback Data:", data)

        # You can access specific fields from the data
        # For example, you might want to check the transaction status
        transaction_status = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
        
        # Implement your logic based on the transaction status
        if transaction_status == '0':  # Assuming '0' means success
            # Handle successful payment, e.g., update order status
            pass
        else:
            # Handle failed payment
            pass

        # Return a success response to M-Pesa
        return JsonResponse({'status': 'success'}, status=200)

    return JsonResponse({'status': 'method not allowed'}, status=405)