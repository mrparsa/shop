from django.urls import path
from . import views

urlpatterns = [
    path('add/cart' , views.cart_add, name='add'),
    path('<int:id>/', views.product_detail, name='product_detail'),
    path('cart' , views.cart_view, name='cart'),

]
