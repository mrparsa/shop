from .models import Product
class Cart() :
    def __init__(self,request):
        self.session = request.session
        cart = self.session.get('session_key')

        if 'session_key' not in request.session:
            cart = self.session['session_key'] = {}

        self.cart = cart    # bara motmaen shodan inke dar hame app ha kar mikonad

     #------------------------------------------------------------------------------------
    def add (self,id,size,tedad):
        product_id = str(id)
        product_quantity = tedad
        product_size = str(size)

        if product_id in self.cart.keys():
            self.cart[product_id]['quantity'] += product_quantity
        else :
            self.cart[product_id] = {'quantity': product_quantity,'size': product_size}

#####################    در حال تست 
        # if product_code in self.cart.keys():
        #     if size is  None :
        #         self.cart[product_code]['quantity'] += product_quantity
        #     else :
        #         if self.cart[product_code]['size'].value() == size :
        #             self.cart[product_code]['quantity'] += product_quantity


        # else :
        #     if size is None:
        #         self.cart[product_code] = {'quantity': product_quantity,'model': product_model}
        #     else :
        #         self.cart[product_code] = {'quantity': product_quantity,'model': product_model ,'size': size}  
##################      

        print(self.cart.items())
        self.session.modified = True

    #     #------------------------------------------------------------------------------------
    # def cart_total (self) :
    #     quantities = self.cart
    #     product_ids = self.cart.keys()
        
    #     man = manto.objects.filter(product_code__in=product_ids)
    #     shal = shal_or_rosari.objects.filter(product_code__in=product_ids)
    #     products = list(man) + list(shal)
    #     total = 0 
    #     for key , value in quantities.items():
    #         key = int(key)
    #         for product in products :
    #             if product.product_code == key :
    #                 total += (product.price *  value.get('quantity'))
    #     return total
            
    #  #------------------------------------------------------------------------------------


    def __len__ (self):
        return len(self.cart)
    #  #------------------------------------------------------------------------------------
    
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
    def get_products (self):
        products_ids = self.cart.keys()
        products = Product.objects.filter(id__in=products_ids)
        return products
        
    #  #------------------------------------------------------------------------------------

    # def get_quants (self) :
    #     quantities = self.cart
    #     return quantities
    #  #------------------------------------------------------------------------------------

    # def delete (self, product_code) :
    #     product_code = str(product_code)
        
    #     if product_code in self.cart :
    #         del self.cart[product_code]
    #     self.session.modified = True
        
    #  #------------------------------------------------------------------------------------
    # def delete_all (self) :
    #     del self.cart
    #     self.session.modified = True
        

    # def items (self):
    #     return self.cart.keys()