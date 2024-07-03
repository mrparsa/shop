from django.contrib import admin
from .models import Product , Chategory , size
# Register your models here.c
admin.site.register(Chategory)
admin.site.register(Product)
admin.site.register(size)