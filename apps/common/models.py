from django.db import models
import uuid
from django.utils import timezone
from .managers import IsDeletedManager
from apps.common.managers import GerOrNoneManager


# Create your models here.


class BaseModel(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = GerOrNoneManager()

    class Meta:
        abstract = True


class IsDeletedModel(BaseModel):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True,blank=True)

    class Meta:
        abstract = True
        ordering = ['-id']
    objects = IsDeletedManager()

    def delete(self,*args,**kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted','deleted_at'])

    def hard_delete(self,*args,**kwargs):
        return super().delete(*args,**kwargs)
