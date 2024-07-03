from django.urls import path
from . import views

urlpatterns = [
    path('',views.home , name = 'home'),
    path('contact_us/',views.contact , name = 'Contact'),
    # path('modaresan/',views.modaresan , name = 'modaresan'),
    # path('about_us/',views.about , name = 'about'),
    # path('modaresan/<int:id>/',views.modaresan_detail , name = 'modares_detail'),
    # path('comment/<int:id>/',views.comment_modares , name = 'comment'),
    # path('<str:x>/', views.akhbar_blog, name='ab'),
    # path('<int:id>/<str:x>', views.akhbar_blog_detail, name='ab_detail'),
    # path('masolan/<int:id>/',views.masolan_detail , name = 'masolan_detail'), 

    # path('<str:x>', views.product, name='product'),
    # path ('serche/' , views.serch, name='serch'),
    # path('add/cart' , views.cart_add, name='add'),
    # path('cart/' , views.cart_views,  name='cart'),
    # path('delete/' , views.cart_delete, name='delete'),
    # path('delete_all/' , views.delete_all, name='delete_all'),

]
