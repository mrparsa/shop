from django.shortcuts import render
from django.shortcuts import render
from django.shortcuts import render , get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
# from django.db.models.functions import Substr
from .models import *
from .cart import Cart
# from django.shortcuts import render, redirect
# from django.urls import reverse
# from django.core.paginator import Paginator 

# from django.contrib.sessions.models import Session
# from django.core.handlers.wsgi import WSGIRequest
# ###

def product_detail (request,id) :
    product = Product.objects.get(id=id)
    return render(request,'product-detail.html',{'product':product})

def cart_add (request):
    cart = Cart(request)
    if request.POST.get('action') == 'post' :
        id = request.POST.get('id')
        # tedad = int(request.POST.get('tedad'))
        tedad = 1
        size = str(request.POST.get('size'))
        print(id, size,tedad)
    

        cart.add(id=id,size=size,tedad=tedad)

        # # get tedad 
        cart_quantity = cart.__len__()       
        # messages.success(request, ("product add to cart ") )
        res = JsonResponse({'qty':cart_quantity})
        return res
        # cart.add(product=product_)
    
def cart_view (request):
    cart = Cart(request)
    products = cart.get_products()
    return render (request,'shoping-cart.html',{'products':products})