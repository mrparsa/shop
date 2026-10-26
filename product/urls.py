from django.urls import path
from . import views

urlpatterns = [
    path('add/cart' , views.cart_add, name='add'),
    path('<int:id>/', views.product_detail, name='product_detail'),
    path('cart/update', views.cart_update, name='cart_update'),
    path('cart/delete', views.cart_delete, name='cart_delete'),
    path('cart/clear', views.cart_clear, name='cart_clear'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<uuid:code>/', views.order_success, name='order_success'),
    path('cart' , views.cart_view, name='cart'),

]
