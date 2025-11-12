from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    phone_number = models.CharField(max_length=10, default="")
    address = models.CharField(max_length=250, default="")
    city = models.CharField(max_length=250, default="")
    state = models.CharField(max_length=250, default="")
    zipcode = models.CharField(max_length=250, default="")
    country = models.CharField(max_length=250, default="")

class Orders(models.Model):
    order_id = models.AutoField(primary_key=True)
    item = models.CharField(max_length=250)
    total = models.DecimalField(decimal_places=2, max_digits=10)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=250, default="Paid")
    order_id = models.CharField(max_length=250, default="")



class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item_id = models.CharField(max_length=100)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    added_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=250, default="Unpaid")