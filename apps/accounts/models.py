from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.common.models import IsDeletedModel
from django.contrib.auth.models import AbstractBaseUser
from apps.accounts.managers import CustomUserManager

# Create your models here.


ACCOUNT_TYPE_CHOICES=(
    ("SELLER","SELLER"),
    ("BUYER","BUYER"),
)


class User(AbstractBaseUser,IsDeletedModel):
    first_name = models.CharField(verbose_name="Имя",max_length=50,null=True)
    last_name = models.CharField(verbose_name="Фамилия",max_length=50, null=True)
    email = models.EmailField(unique=True,verbose_name="Почта",)
    avatar = models.ImageField(upload_to="avatars/",null=True,default="avatars/default.jpg")

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    account_type = models.CharField(max_length=6,choices=ACCOUNT_TYPE_CHOICES,default="BUYER")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name","last_name"]

    objects = CustomUserManager()


    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return  True

    @property
    def is_superuser(self):
        return self.is_staff