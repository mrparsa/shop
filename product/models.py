from django.db import models
from tinymce.models import HTMLField

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
    size = models.ManyToManyField(size,blank=True)
    image = models.ImageField(upload_to='images_product/')
    quantity = models.IntegerField(default=1,blank=True)
    price = models.FloatField()
    Discount = models.BooleanField(default=False , null=True)
    Discount_price = models.IntegerField(blank=True , null=True)

    def __str__(self) -> str:
        return self.title
    # def m (self) :
    #     slug = 'shalvar' + self.code
    #     return slug
    def model_name(self):
        return self.__class__.__name__