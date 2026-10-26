from decimal import Decimal
from django.core.exceptions import ValidationError
from .models import Product


class Cart():
    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.setdefault('session_key', {})
        # Keep carts from the old product-id format usable.
        for key, item in list(self.cart.items()):
            if ':' not in key:
                self.cart.pop(key)
                self.save()
                try:
                    product = Product.objects.get(pk=key)
                    sizes = list(product.size.all())
                    selected = next((s for s in sizes if str(item.get('size')) in
                                     (str(s.pk), str(s), 'Size ' + str(s))), None)
                    if sizes and selected is None:
                        continue
                    size_id = str(selected.pk) if selected else ''
                    self.cart[f'{product.pk}:{size_id}'] = {
                        'product_id': product.pk, 'size': size_id,
                        'quantity': max(1, int(item['quantity']))}
                except (Product.DoesNotExist, ValueError, TypeError, KeyError):
                    pass
                self.save()

    def save(self):
        self.session.modified = True

    def add(self, id, size, tedad, replace=False):
        product = Product.objects.get(pk=id)
        try:
            quantity = int(tedad)
        except (ValueError, TypeError):
            raise ValidationError('تعداد باید عدد صحیح باشد.')
        if quantity < 1:
            raise ValidationError('تعداد باید حداقل یک باشد.')
        stocks = {str(stock.size_id): stock for stock in product.size_stocks.all()}
        selected = str(size or '')
        if stocks and selected not in stocks:
            raise ValidationError('سایز معتبر محصول را انتخاب کنید.')
        if not stocks and selected:
            raise ValidationError('این محصول سایز انتخابی ندارد.')
        key = f'{product.pk}:{selected}'
        current = self.cart.get(key, {}).get('quantity', 0)
        quantity = quantity if replace else current + quantity
        available = stocks[selected].quantity if stocks else product.quantity
        if quantity > available:
            raise ValidationError('تعداد درخواستی بیشتر از موجودی سایز یا محصول انتخاب‌شده است.')
        self.cart[key] = {'product_id': product.pk, 'size': selected, 'quantity': quantity}
        self.save()

    def __iter__(self):
        products = {p.pk: p for p in self.get_products()}
        for key, item in list(self.cart.items()):
            product = products.get(item['product_id'])
            if product is None:
                self.delete(key)
                continue
            stocks = {str(stock.size_id): stock for stock in product.size_stocks.all()}
            stock = stocks.get(item['size'])
            valid = stock is not None if stocks else not item['size']
            available = stock.quantity if stock else (0 if item['size'] or stocks else product.quantity)
            yield {**item, 'key': key, 'product': product,
                   'size_name': str(stock.size) if stock else ('سایز حذف‌شده' if item['size'] else 'بدون سایز'),
                   'available': available,
                   'valid': valid and item['quantity'] <= available,
                   'price': product.final_price,
                   'total': product.final_price * item['quantity']}

    def __len__(self):
        return sum(item['quantity'] for item in self)

    def get_products(self):
        ids = [item['product_id'] for item in self.cart.values()]
        return Product.objects.filter(pk__in=ids).prefetch_related('size_stocks__size')

    def cart_total(self):
        return sum((item['total'] for item in self), Decimal('0'))

    def delete(self, key):
        self.cart.pop(key, None)
        self.save()

    def delete_all(self):
        self.cart.clear()
        self.save()
