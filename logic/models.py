from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    phone_number = models.CharField(max_length=15, default="", blank=True)
    address = models.CharField(max_length=250, default="", blank=True)
    city = models.CharField(max_length=250, default="", blank=True)
    appartament = models.CharField(max_length=250, default="", blank=True)
    state = models.CharField(max_length=250, default="", blank=True)
    zipcode = models.CharField(max_length=20, default="", blank=True)
    country = models.CharField(max_length=250, default="", blank=True)

    def __str__(self):
        return self.username


class Orders(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    item = models.CharField(max_length=250)
    total = models.DecimalField(decimal_places=2, max_digits=10)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="Paid")
    order_id = models.CharField(max_length=250, default="", unique=True)

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Orders"

    def get_items_list(self):
        return [item.strip() for item in self.item.split(',') if item.strip()]


class CartItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    item_id = models.CharField(max_length=100)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    added_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="Unpaid")

    class Meta:
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.item_id}"