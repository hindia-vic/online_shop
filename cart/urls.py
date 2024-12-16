from django.urls import path
from .views import cart_item,cart_detail,cart_remove

urlpatterns=[
    path('add/<int:product_id>/',cart_item,name='cart_add'),
    path('',cart_detail,name='cart_detail'),
    path('remove/<int:product_id>/',cart_remove,name='remove_cart'),
]