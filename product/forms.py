from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    phone = forms.RegexField(regex=r'^09[0-9]{9}$', label='شماره موبایل',
                            error_messages={'invalid': 'شماره موبایل را با 09 و یازده رقم وارد کنید.'})
    postal_code = forms.RegexField(regex=r'^[0-9]{10}$', label='کد پستی',
                                  error_messages={'invalid': 'کد پستی باید ده رقم باشد.'})

    class Meta:
        model = Order
        fields = ('full_name', 'phone', 'address', 'postal_code')
        labels = {'full_name': 'نام و نام خانوادگی', 'address': 'نشانی کامل'}
        widgets = {'address': forms.Textarea(attrs={'rows': 3})}
