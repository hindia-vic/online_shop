from django.urls import path
from .views import order_create,order_confirmation,OrdersPageView,charge,initiate_payment,payment_callback,get_mpesa_access_token,stk_status_view

"""urlpatterns=[
    path('charge/<int:order_id>/',charge,name='charge'),
    path('create',order_create,name='order_create'),
    path('confrimation/<int:order_id>/',order_confirmation,name='order_confirmation'),
    path('<int:order_id>/', OrdersPageView.as_view(), name='orders'), 
    path('initiate-payment/<int:order_id>/', initiate_payment, name='initiate_payment'),
    path('callback/', mpesa_callback, name='mpesa_callback'),
    #path('accesstoken/',get_mpesa_access_token,name='access_token'),
]"""
urlpatterns = [
    path('charge/<int:order_id>/', charge, name='charge'),
    path('create/', order_create, name='order_create'),
    path('confirmation/<int:order_id>/', order_confirmation, name='order_confirmation'),
    path('order/<int:order_id>/', OrdersPageView.as_view(), name='orders'),
    path('initiate-payment/<int:order_id>/', initiate_payment, name='initiate_payment'),
    path('callback/', payment_callback, name='mpesa_callback'),
    path('stk_status/', stk_status_view, name='stk-status'),
    # Uncomment if needed
    # path('accesstoken/', get_mpesa_access_token, name='access_token'),
]