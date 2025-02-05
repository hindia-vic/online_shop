from django.shortcuts import render,redirect,get_object_or_404
from cart.models import Cart
from .forms import OrderCreateForm
from .models import Orderitem,Order,Transaction
from django.conf import settings
from django.views.generic.base import TemplateView
from django.http import JsonResponse,HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json 
import stripe
import requests
import base64
import datetime
import logging

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY
MPESA_SHORTCODE=settings.MPESA_SHORTCODE
MPESA_PASSKEY=settings.MPESA_PASSKEY
MPESA_BASE_URL=settings.MPESA_BASEURL



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
        return access_token
  
    else:
        print(f"Error Response: {response.content}")
        raise Exception('Failed to get access token')
       

def lipa_na_mpesa(phone_number, amount,transaction_desc,order_id):
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
        "CallBackURL": "https://8197-102-211-145-195.ngrok-free.app/order/callback/",  # Replace with your callback endpoint
        "AccountReference":order_id,
        "TransactionDesc": transaction_desc,
    }

    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()
def initiate_payment(request,order_id):
    order = get_object_or_404(Order, id=order_id)
    price = int(order.get_total_cost())
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')  # Input from user
        amount =price # Input from user

        response = lipa_na_mpesa(phone_number, amount, order_id, "Payment for order")
        
        if response.get('ResponseCode') == '0':
            checkout_request_id = response["CheckoutRequestID"]
            success_message = "M-Pesa STK Push sent successfully. Enter your M-Pesa PIN to complete the transaction."
            return render(
                request, "product/pending.html", 
                {"checkout_request_id": checkout_request_id, "success_message": success_message}
            )
        else:
            error_message = response.get("errorMessage", "Failed to send STK push. Please try again.")
            return render(request, "product/initiate_payment.html", {"error_message": error_message})
    
    return render(request, 'product/initiate_payment.html')

def query_stk_push(checkout_request_id):
    print("Quering...")
    try:
        token = get_mpesa_access_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(
            (MPESA_SHORTCODE + MPESA_PASSKEY + timestamp).encode()
        ).decode()

        request_body = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }

        response = requests.post(
            f"{MPESA_BASE_URL}/mpesa/stkpushquery/v1/query",
            json=request_body,
            headers=headers,
        )
        print(response.json())
        return response.json()

    except requests.RequestException as e:
        print(f"Error querying STK status: {str(e)}")
        return {"error": str(e)}

def stk_status_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            checkout_request_id = data.get('checkout_request_id')

            status_response = query_stk_push(checkout_request_id)

            result_code = status_response.get("ResultCode")

            if result_code == '0':
                return JsonResponse({"status": "success", "message": "Payment successful. Redirecting..."})
            elif result_code == '1':
                return JsonResponse({"status": "failed", "message": "Payment failed. Please try again."})
            else:
                return JsonResponse({"status": "pending", "message": "Waiting for confirmation..."})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON body"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def payment_callback(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST requests allowed.")

    try:
        callback_data = json.loads(request.body)
        logger.info(f"Received M-Pesa Callback: {json.dumps(callback_data, indent=4)}")

        result_code = callback_data["Body"]["stkCallback"]["ResultCode"]
        if result_code == 0:
            checkout_id = callback_data["Body"]["stkCallback"]["CheckoutRequestID"]
            metadata = callback_data["Body"]["stkCallback"]["CallbackMetadata"]["Item"]

            amount = next(item["Value"] for item in metadata if item["Name"] == "Amount")
            mpesa_code = next(item["Value"] for item in metadata if item["Name"] == "MpesaReceiptNumber")
            phone_number = next(item["Value"] for item in metadata if item["Name"] == "PhoneNumber")

            with transaction.atomic():
                if Transaction.objects.filter(mpesa_code=mpesa_code).exists():
                    return JsonResponse({"ResultCode": 1, "ResultDesc": "Duplicate transaction"})

                order = Order.objects.filter(transactions__checkout_id=callback_data["Body"]["stkCallback"]["MerchantRequestID"]).first()

                if not order:
                    return JsonResponse({"ResultCode": 1, "ResultDesc": "Order not found"})

                Transaction.objects.create(
                    amount=amount,
                    order=order,
                    checkout_id=checkout_id,
                    mpesa_code=mpesa_code,
                    phone_number=phone_number,
                    status="completed",
                )

                order.mark_as_paid()  # Ensure order is marked as paid
                return JsonResponse({"ResultCode": 0, "ResultDesc": "Payment successfully processed."})

        return JsonResponse({"ResultCode": result_code, "ResultDesc": "Payment failed"})

    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON data received.")
    except KeyError as e:
        return HttpResponseBadRequest(f"Missing key in response: {str(e)}")

