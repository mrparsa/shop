from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
import uuid

gender_choice= (
    ('male', 'male'),
    ('female', 'female'),
)

class Chategory (models.Model):
    Chategory = models.CharField(max_length=100)
    def __str__(self) -> str:
        return self.Chategory
class size (models.Model):
    size = models.CharField(max_length=100)
    def __str__(self) -> str:
        return self.size
#----------------------------
    
class Product(models.Model):
    category = models.ForeignKey(Chategory , on_delete=models.CASCADE)
    gender = models.CharField(max_length=100,choices=gender_choice)
    title = models.CharField(max_length=100)
    text = models.TextField()
    size = models.ManyToManyField(size, through='ProductSize', blank=True)
    image = models.ImageField(upload_to='images_product/')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    Discount = models.BooleanField(default=False , null=True)
    Discount_price = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])

    def __str__(self) -> str:
        return self.title
    def model_name(self):
        return self.__class__.__name__

    @property
    def final_price(self):
        if self.Discount and self.Discount_price is not None:
            return self.Discount_price
        return self.price

    @property
    def total_quantity(self):
        stocks = list(self.size_stocks.all())
        if stocks:
            return sum(stock.quantity for stock in stocks)
        return self.quantity

    def clean(self):
        super().clean()
        if self.Discount and self.Discount_price is None:
            raise ValidationError({'Discount_price': 'قیمت تخفیف را وارد کنید.'})
        if self.Discount and self.Discount_price is not None and self.price is not None:
            if self.Discount_price > self.price:
                raise ValidationError({'Discount_price': 'قیمت تخفیف نباید بیشتر از قیمت اصلی باشد.'})


class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='size_stocks')
    size = models.ForeignKey(size, on_delete=models.PROTECT, verbose_name='سایز')
    quantity = models.PositiveIntegerField(default=0, verbose_name='موجودی')

    class Meta:
        verbose_name = 'موجودی سایز'
        verbose_name_plural = 'موجودی سایزها'
        constraints = [models.UniqueConstraint(fields=('product', 'size'), name='unique_product_size')]

    def __str__(self):
        return f'{self.product} - {self.size}'


class Order(models.Model):
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    postal_code = models.CharField(max_length=10)
    total = models.DecimalField(max_digits=16, decimal_places=2)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.full_name} - {self.code}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=100)
    size = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=14, decimal_places=2)

    @property
    def total(self):
        return self.price * self.quantity

    def __str__(self):
        return self.title
