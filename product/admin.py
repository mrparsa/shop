from django.contrib import admin
from .models import Product, Chategory, size, ProductSize, Order, OrderItem


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'gender', 'price', 'Discount', 'Discount_price', 'stock_total')
    list_filter = ('category', 'gender', 'Discount')
    search_fields = ('title', 'text')
    inlines = (ProductSizeInline,)
    list_select_related = ('category',)
    readonly_fields = ('stock_total',)
    fields = ('title', 'category', 'gender', 'text', 'image', 'quantity', 'stock_total',
              'price', 'Discount', 'Discount_price')

    @admin.display(description='موجودی کل')
    def stock_total(self, obj):
        return obj.total_quantity if obj and obj.pk else 0

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['quantity'].label = 'موجودی محصول بدون سایز'
        form.base_fields['quantity'].help_text = 'برای محصول سایزدار، موجودی هر سایز را در جدول پایین وارد کنید؛ این عدد استفاده نمی‌شود.'
        return form

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('size_stocks')


admin.site.register(Chategory)
admin.site.register(size)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ('product', 'title', 'size', 'quantity', 'price', 'total')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('code', 'full_name', 'phone', 'total', 'created')
    search_fields = ('full_name', 'phone', 'code')
    readonly_fields = ('code', 'full_name', 'phone', 'address', 'postal_code', 'total', 'created')
    inlines = (OrderItemInline,)

    def has_add_permission(self, request):
        return False
