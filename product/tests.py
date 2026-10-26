from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, TransactionTestCase
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.urls import reverse
from .models import Chategory, Product, ProductSize, size, Order


class ShopTests(TestCase):
    def setUp(self):
        self.category = Chategory.objects.create(Chategory='Clothes')
        self.small = size.objects.create(size='S')
        self.large = size.objects.create(size='L')
        self.product = Product.objects.create(
            title='Shirt', text='Cotton shirt', category=self.category,
            gender='male', quantity=5, price=Decimal('100.50'),
            Discount=True, Discount_price=Decimal('80.25'))
        self.small_stock = ProductSize.objects.create(product=self.product, size=self.small, quantity=5)
        self.large_stock = ProductSize.objects.create(product=self.product, size=self.large, quantity=3)
        self.delivery = {'full_name': 'Test Customer', 'phone': '09123456789',
                         'postal_code': '1234567890', 'address': 'Test address'}

    def add(self, quantity=1, selected=None, **extra):
        return self.client.post(reverse('add'), {
            'id': self.product.pk, 'size': selected or self.small.pk,
            'tedad': quantity, **extra}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def test_pages_and_actual_product_links(self):
        for name in ('home', 'cart'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        detail = self.client.get(reverse('product_detail', args=[self.product.pk]))
        self.assertContains(detail, 'انتخاب سایز')
        self.assertContains(detail, 'افزودن به سبد خرید')
        self.assertNotContains(detail, 'جنسیت')
        self.assertEqual(self.client.get(reverse('product_detail', args=[999])).status_code, 404)
        self.assertContains(self.client.get(reverse('home')), reverse('product_detail', args=[self.product.pk]))

    def test_sizes_are_separate_and_discount_total_is_exact(self):
        self.assertEqual(self.add(2).json()['qty'], 2)
        response = self.add(1, self.large.pk)
        self.assertEqual(response.json()['qty'], 3)
        self.assertEqual(response.json()['total'], '240.75')
        self.assertEqual(len(self.client.session['session_key']), 2)
        self.assertContains(self.client.get(reverse('cart')), 'Shirt')
        self.assertContains(self.client.get(reverse('checkout')), 'ثبت سفارش آزمایشی')

    def test_stock_is_independent_for_each_size(self):
        self.add(3)
        self.assertEqual(self.add(3, self.large.pk).status_code, 200)
        self.assertEqual(len(self.client.session['session_key']), 2)
        self.assertEqual(self.add(1, self.large.pk).status_code, 400)

    def test_invalid_quantities_and_sizes(self):
        for quantity in ('0', '-2', '1.5', 'abc', '6'):
            self.assertEqual(self.add(quantity).status_code, 400)
        self.assertEqual(self.add(selected=999).status_code, 400)
        response = self.client.post(reverse('add'), {'id': self.product.pk, 'tedad': 1},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.client.post(reverse('add'), {'id': 'bad'}).status_code, 404)

    def test_product_without_size(self):
        self.product.size.clear()
        response = self.client.post(reverse('add'), {'id': self.product.pk, 'tedad': 2},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.json()['qty'], 2)
        self.assertContains(self.client.get(reverse('cart')), 'بدون سایز')

    def test_update_delete_clear(self):
        self.add(2)
        key = f'{self.product.pk}:{self.small.pk}'
        self.client.post(reverse('cart_update'), {'key': key, 'tedad': 4})
        self.assertEqual(self.client.session['session_key'][key]['quantity'], 4)
        self.client.post(reverse('cart_delete'), {'key': key})
        self.assertEqual(self.client.session['session_key'], {})
        self.add()
        self.client.post(reverse('cart_clear'))
        self.assertEqual(self.client.session['session_key'], {})

    def test_mutations_require_post_and_csrf(self):
        for name in ('add', 'cart_update', 'cart_delete', 'cart_clear'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 405)
            self.assertEqual(Client(enforce_csrf_checks=True).post(reverse(name)).status_code, 403)

    def test_deleted_product_is_removed(self):
        self.add()
        self.product.delete()
        self.assertContains(self.client.get(reverse('cart')), 'سبد خرید شما خالی است.')
        self.assertEqual(self.client.session['session_key'], {})

    def test_old_session_cart_is_migrated(self):
        session = self.client.session
        session['session_key'] = {str(self.product.pk): {'quantity': 2, 'size': 'Size S'}}
        session.save()
        self.assertEqual(self.client.get(reverse('cart')).status_code, 200)
        self.assertIn(f'{self.product.pk}:{self.small.pk}', self.client.session['session_key'])

    def test_checkout_stores_snapshot_and_reduces_stock(self):
        self.add(2)
        self.add(1, self.large.pk)
        response = self.client.post(reverse('checkout'), self.delivery)
        order = Order.objects.get()
        self.assertRedirects(response, reverse('order_success', args=[order.code]))
        self.assertEqual(order.total, Decimal('240.75'))
        self.assertEqual(order.items.count(), 2)
        admin = get_user_model().objects.create_superuser(username='order-admin', password='test-password')
        admin_client = Client()
        admin_client.force_login(admin)
        self.assertEqual(admin_client.get(reverse('admin:product_order_change', args=[order.pk])).status_code, 200)
        self.product.refresh_from_db()
        self.small_stock.refresh_from_db()
        self.large_stock.refresh_from_db()
        self.assertEqual(self.small_stock.quantity, 3)
        self.assertEqual(self.large_stock.quantity, 2)
        self.assertEqual(self.product.total_quantity, 5)
        self.assertEqual(self.product.quantity, 5)
        self.assertEqual(self.client.session['session_key'], {})
        self.client.post(reverse('checkout'), self.delivery)
        self.assertEqual(Order.objects.count(), 1)
        self.product.delete()
        self.assertEqual(order.items.first().title, 'Shirt')

    def test_insufficient_stock_rolls_back_all_lines(self):
        self.add(2)
        self.add(2, self.large.pk)
        ProductSize.objects.filter(pk=self.large_stock.pk).update(quantity=1)
        response = self.client.post(reverse('checkout'), self.delivery)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].non_field_errors())
        self.small_stock.refresh_from_db()
        self.large_stock.refresh_from_db()
        self.assertEqual(self.small_stock.quantity, 5)
        self.assertEqual(self.large_stock.quantity, 1)
        self.assertFalse(Order.objects.exists())
        self.assertEqual(len(self.client.session['session_key']), 2)

    def test_checkout_uses_current_price(self):
        self.add()
        Product.objects.filter(pk=self.product.pk).update(Discount_price=Decimal('75.10'))
        self.client.post(reverse('checkout'), self.delivery)
        self.assertEqual(Order.objects.get().total, Decimal('75.10'))

    def test_removed_size_blocks_checkout(self):
        self.add()
        self.product.size.remove(self.small)
        response = self.client.post(reverse('checkout'), self.delivery)
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertFalse(Order.objects.exists())

    def test_invalid_delivery_and_order_privacy(self):
        self.add()
        response = self.client.post(reverse('checkout'), {**self.delivery, 'phone': 'abc'})
        self.assertIn('phone', response.context['form'].errors)
        self.assertFalse(Order.objects.exists())
        self.client.post(reverse('checkout'), self.delivery)
        order = Order.objects.get()
        self.assertEqual(Client().get(reverse('order_success', args=[order.code])).status_code, 404)

    def test_product_admin_and_validation(self):
        user = get_user_model().objects.create_superuser(username='admin', password='test-password')
        self.client.force_login(user)
        for url in ('admin:product_product_add', 'admin:product_order_changelist'):
            self.assertEqual(self.client.get(reverse(url)).status_code, 200)
        self.product.Discount_price = Decimal('200')
        with self.assertRaises(ValidationError):
            self.product.full_clean(exclude=['image'])

    def test_search_and_category_filter(self):
        self.assertContains(self.client.get(reverse('home'), {'q': 'Cotton'}), 'Shirt')
        self.assertNotContains(self.client.get(reverse('home'), {'q': 'No match'}), '>Shirt<')
        self.assertContains(self.client.get(reverse('home'), {'category': self.category.pk}), 'Shirt')
        self.assertNotContains(self.client.get(reverse('home'), {'gender': 'female'}), '>Shirt<')

    def test_sized_product_ignores_unsized_stock(self):
        Product.objects.filter(pk=self.product.pk).update(quantity=0)
        self.assertEqual(self.add(2).status_code, 200)
        self.assertContains(self.client.get(reverse('home')), 'انتخاب سایز و خرید')
        self.assertContains(self.client.get(reverse('product_detail', args=[self.product.pk])), 'موجودی کل: 8')

    def test_out_of_stock_size_does_not_block_other_sizes(self):
        ProductSize.objects.filter(pk=self.small_stock.pk).update(quantity=0)
        self.assertEqual(self.add().status_code, 400)
        self.assertEqual(self.add(selected=self.large.pk).status_code, 200)
        response = self.client.get(reverse('product_detail', args=[self.product.pk]))
        self.assertContains(response, f'value="{self.small.pk}" data-quantity="0" disabled')

    def test_unsized_checkout_reduces_product_stock(self):
        self.product.size.clear()
        self.client.post(reverse('add'), {'id': self.product.pk, 'tedad': 2})
        self.client.post(reverse('checkout'), self.delivery)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 3)
        self.assertEqual(Order.objects.get().items.get().size, 'بدون سایز')

    def test_admin_can_edit_size_stock_inline(self):
        user = get_user_model().objects.create_superuser(username='stock-admin', password='test-password')
        self.client.force_login(user)
        self.product.image = 'images_product/test.jpg'
        self.product.save()
        response = self.client.post(reverse('admin:product_product_change', args=[self.product.pk]), {
            'title': self.product.title, 'text': self.product.text,
            'category': self.category.pk, 'gender': 'male', 'quantity': 0,
            'price': '100.50', 'Discount': 'True', 'Discount_price': '80.25',
            'size_stocks-TOTAL_FORMS': 2, 'size_stocks-INITIAL_FORMS': 2,
            'size_stocks-MIN_NUM_FORMS': 0, 'size_stocks-MAX_NUM_FORMS': 1000,
            'size_stocks-0-id': self.small_stock.pk, 'size_stocks-0-product': self.product.pk,
            'size_stocks-0-size': self.small.pk, 'size_stocks-0-quantity': 10,
            'size_stocks-1-id': self.large_stock.pk, 'size_stocks-1-product': self.product.pk,
            'size_stocks-1-size': self.large.pk, 'size_stocks-1-quantity': 0,
            '_save': 'Save',
        })
        self.assertEqual(response.status_code, 302)
        self.small_stock.refresh_from_db()
        self.large_stock.refresh_from_db()
        self.assertEqual(self.small_stock.quantity, 10)
        self.assertEqual(self.large_stock.quantity, 0)


class SizeStockMigrationTests(TransactionTestCase):
    def test_existing_stock_and_sizes_survive_migration_and_rollback(self):
        old_target = [('product', '0004_order_alter_product_discount_price_and_more')]
        new_target = [('product', '0005_productsize_alter_product_size_and_more')]
        executor = MigrationExecutor(connection)
        try:
            executor.migrate(old_target)
            old_apps = executor.loader.project_state(old_target).apps
            OldProduct = old_apps.get_model('product', 'Product')
            category = old_apps.get_model('product', 'Chategory').objects.create(Chategory='Clothes')
            small = old_apps.get_model('product', 'size').objects.create(size='S')
            large = old_apps.get_model('product', 'size').objects.create(size='L')
            product = OldProduct.objects.create(title='Old shirt', category=category,
                                               gender='male', quantity=5, price=100)
            product.size.set([small, large])
            unsized = OldProduct.objects.create(title='Scarf', category=category,
                                               gender='female', quantity=7, price=100)
            executor = MigrationExecutor(connection)
            executor.migrate(new_target)
            new_apps = executor.loader.project_state(new_target).apps
            NewProduct = new_apps.get_model('product', 'Product')
            stocks = new_apps.get_model('product', 'ProductSize').objects.filter(product_id=product.pk)
            self.assertEqual(list(stocks.order_by('size_id').values_list('quantity', flat=True)), [3, 2])
            self.assertEqual(NewProduct.objects.get(pk=product.pk).quantity, 0)
            self.assertEqual(NewProduct.objects.get(pk=product.pk).size.count(), 2)
            self.assertEqual(NewProduct.objects.get(pk=unsized.pk).quantity, 7)
            executor = MigrationExecutor(connection)
            executor.migrate(old_target)
            restored_apps = executor.loader.project_state(old_target).apps
            restored = restored_apps.get_model('product', 'Product').objects.get(pk=product.pk)
            self.assertEqual(restored.quantity, 5)
            self.assertEqual(restored.size.count(), 2)
        finally:
            MigrationExecutor(connection).migrate(new_target)
