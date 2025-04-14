from django.contrib.auth.base_user import BaseUserManager
from django.core.validators import validate_email
from rest_framework.exceptions import ValidationError


class CustomUserManager(BaseUserManager):
    def email_validator(self,email):
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Не правильный email")

    def validate_user(self,first_name,last_name,email):
        if not first_name:
            raise  ValidationError("Не заданно имя")

        if not last_name:
            raise ValidationError("Не задана фамилия")

        if email:
            email = self.normalize_email(email)
            self.email_validator(email)
        else:
            raise ValidationError("Не задана почта")

    def create_user(self,first_name,last_name,email,password,**extra_fields):
        self.validate_user(first_name,last_name,email)

        user = self.model(
            first_name=first_name,last_name=last_name,email=email, **extra_fields
        )

        user.set_password(password)
        extra_fields.setdefault("is_staff",False)
        user.save()
        return user

    def validate_superuser(self,email,password,**extra_fields):
        extra_fields.setdefault("is_staff",True)
        extra_fields.setdefault("is_superuser",True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusers must have is_staff=True")

        if not password:
            raise ValueError("Superusers must have a password")

        if email:
            email = self.normalize_email(email)
            self.email_validator(email)
        else:
            raise ValueError("Admin Account: An email address is required")
        return extra_fields

    def create_superuser(self, first_name, last_name, email, password, **extra_fields):
        extra_fields = self.validate_superuser(email, password, **extra_fields)
        user = self.create_user(first_name, last_name, email, password, **extra_fields)
        return user