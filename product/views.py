from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, JsonResponse
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.views.decorators.http import require_POST
from .models import Product, ProductSize, Order, OrderItem
from .cart import Cart
from .forms import CheckoutForm


def product_detail(request, id):
    product = get_object_or_404(Product.objects.prefetch_related('size_stocks__size'), id=id)
    return render(request, 'product-detail.html', {'product': product})


def cart_result(request, cart, error=None):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'qty': len(cart), 'total': str(cart.cart_total()),
                             'error': error}, status=400 if error else 200)
    if error:
        messages.error(request, error)
    else:
        messages.success(request, 'سبد خرید به‌روز شد.')
    return redirect('cart')


@require_POST
def cart_add(request):
    cart = Cart(request)
    product = get_object_or_404(Product, pk=request.POST.get('id') if str(request.POST.get('id', '')).isdigit() else 0)
    try:
        cart.add(product.pk, request.POST.get('size'), request.POST.get('tedad', '1'))
    except ValidationError as error:
        return cart_result(request, cart, ' '.join(error.messages))
    return cart_result(request, cart)


def cart_view(request):
    return render(request, 'shoping-cart.html')


@require_POST
def cart_update(request):
    cart = Cart(request)
    item = cart.cart.get(request.POST.get('key'))
    if item is None:
        return cart_result(request, cart, 'این مورد در سبد خرید وجود ندارد.')
    try:
        cart.add(item['product_id'], item['size'], request.POST.get('tedad'), replace=True)
    except (ValidationError, Product.DoesNotExist) as error:
        return cart_result(request, cart, ' '.join(error.messages) if isinstance(error, ValidationError) else 'محصول حذف شده است.')
    return cart_result(request, cart)


@require_POST
def cart_delete(request):
    cart = Cart(request)
    cart.delete(request.POST.get('key'))
    return cart_result(request, cart)


@require_POST
def cart_clear(request):
    cart = Cart(request)
    cart.delete_all()
    return cart_result(request, cart)


def checkout(request):
    cart = Cart(request)
    items = list(cart)
    if not items:
        messages.error(request, 'سبد خرید خالی است.')
        return redirect('cart')
    form = CheckoutForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                # Conditional stock updates also protect against simultaneous purchases.
                products = {p.pk: p for p in Product.objects.select_for_update().filter(
                    pk__in=[item['product_id'] for item in items]).prefetch_related('size_stocks__size')}
                for item in items:
                    product = products.get(item['product_id'])
                    if product is None:
                        raise ValidationError('یکی از محصولات حذف شده است؛ سبد را بررسی کنید.')
                    stocks = {str(stock.size_id): stock for stock in product.size_stocks.all()}
                    if (stocks and item['size'] not in stocks) or (not stocks and item['size']):
                        raise ValidationError('سایز یکی از محصولات تغییر کرده است؛ آن را دوباره به سبد اضافه کنید.')
                    if stocks:
                        stock = stocks[item['size']]
                        inventory = ProductSize.objects.filter(pk=stock.pk)
                        item['size_name'] = str(stock.size)
                    else:
                        inventory = Product.objects.filter(pk=product.pk)
                    updated = inventory.filter(quantity__gte=item['quantity']).update(
                        quantity=F('quantity') - item['quantity'])
                    if not updated:
                        raise ValidationError(f'موجودی {product.title} ({item["size_name"]}) کافی نیست.')
                    item['price'] = product.final_price
                    item['total'] = product.final_price * item['quantity']
                order = form.save(commit=False)
                order.total = sum(item['total'] for item in items)
                order.save()
                for item in items:
                    OrderItem.objects.create(order=order, product=products[item['product_id']],
                        title=products[item['product_id']].title, size=item['size_name'],
                        quantity=item['quantity'], price=item['price'])
            cart.delete_all()
            request.session['last_order'] = str(order.code)
            return redirect('order_success', code=order.code)
        except ValidationError as error:
            form.add_error(None, error)
    return render(request, 'checkout.html', {'form': form})


def order_success(request, code):
    if request.session.get('last_order') != str(code):
        raise Http404
    order = get_object_or_404(Order, code=code)
    return render(request, 'order-success.html', {'order': order})
