from autoslug import AutoSlugField
from django.db import models

from apps.common.models import BaseModel
from ..common.models import IsDeletedModel
from ..sellers.models import Seller
from apps.profiles.models import User

# Create your models here.

class Category(BaseModel):
    name = models.CharField(max_length=100,unique=True)
    slug = AutoSlugField(populate_from="name",always_update=True)
    image = models.ImageField(upload_to="category_image/")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Product(IsDeletedModel):
    seller = models.ForeignKey(Seller,on_delete=models.SET_NULL, related_name="products",null=True)
    name = models.CharField(max_length=100)
    slug = AutoSlugField(populate_from="name", db_index=True)
    desc = models.TextField()
    price_old = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    price_current = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    in_stock = models.IntegerField(default=5)

    # Only 3 images are allowed
    image1 = models.ImageField(upload_to='product_images/')
    image2 = models.ImageField(upload_to='product_images/', blank=True)


    def __str__(self):
        return str(self.name)



RAITING_CHOICES=(
    (1,1),
    (2,2),
    (3,3),
    (4,4),
    (5,5)
)

class Review(IsDeletedModel):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='user')
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RAITING_CHOICES)
    text = models.TextField(max_length=1000)

    def __str__(self):
        return f"{self.user.full_name}'s review for {self.product.name}"

