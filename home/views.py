from django.shortcuts import render
from product.models import Product , Chategory
# Create your views here.
def home(request):
    all_products = Product.objects.all()
    women_products = Product.objects.filter(gender = 'female')
    category = Chategory.objects.all()
    
    return render(request,'home.html',{'all_products':all_products,'category':category})

def contact(request):
    return render(request,'contact.html')