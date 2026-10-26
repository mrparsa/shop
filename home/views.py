from django.shortcuts import render
from django.db.models import Q
from product.models import Product, Chategory


def home(request):
    all_products = Product.objects.select_related('category').prefetch_related('size_stocks').all().order_by('-id')
    search = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', '')
    selected_gender = request.GET.get('gender', '')
    if search:
        all_products = all_products.filter(Q(title__icontains=search) | Q(text__icontains=search))
    if selected_category.isdigit():
        all_products = all_products.filter(category_id=selected_category)
    if selected_gender in ('male', 'female'):
        all_products = all_products.filter(gender=selected_gender)
    return render(request, 'home.html', {
        'all_products': all_products, 'category': Chategory.objects.all(),
        'search': search, 'selected_category': selected_category,
        'selected_gender': selected_gender})


def contact(request):
    return render(request, 'contact.html')
