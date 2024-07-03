from .cart import Cart

def cart (request):
    return {'cart' : Cart(request)}

# def cart_object (request):
#     cart_ = Cart(request)
#     product = cart_
#     for key , value in cart_.items() :
        

    
   # def get_products (self):
    #     product_ids = self.cart
    
    #     items_shal = {}
    #     items_manto = {}
    #     for key, value in product_ids.items():
    #         if value.get('model') == 'manto':
    #             items_manto[key] = value
    #         manto_object = items_manto.keys()

    #         if value.get('model') == 'shal_or_rosari':
    #             items_shal[key] = value

    #     products_manto = manto.objects.filter(product_code__in = items_manto.keys())
    #     products_shal = shal_or_rosari.objects.filter(product_code__in = items_shal.keys())
    #     pro = list(products_manto)+list(products_shal)

    #     return pro