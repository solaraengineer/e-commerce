from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    """Extended user model with shipping/contact info"""
    phone_number = models.CharField(max_length=15, default="", blank=True)
    address = models.CharField(max_length=250, default="", blank=True)
    city = models.CharField(max_length=250, default="", blank=True)
    state = models.CharField(max_length=250, default="", blank=True)
    zipcode = models.CharField(max_length=20, default="", blank=True)
    country = models.CharField(max_length=250, default="", blank=True)

    def __str__(self):
        return self.username


class Orders(models.Model):
    """
    Order model - stores completed purchases

    RECOMMENDED UPGRADE:
    Change user_id from CharField to ForeignKey for proper DB relations
    This would require a migration but is much better practice
    """
    # CURRENT (works with your existing DB)
    user_id = models.CharField(max_length=250, default="")

    # RECOMMENDED (better structure - uncomment this and remove above line)
    # user = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.CASCADE,
    #     related_name='orders'
    # )

    item = models.CharField(max_length=250)  # Comma-separated item names
    total = models.DecimalField(decimal_places=2, max_digits=10)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="Paid")
    order_id = models.CharField(max_length=250, default="", unique=True)

    class Meta:
        ordering = ['-date']  # Most recent first
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order {self.order_id}"

    def get_items_list(self):
        """Helper method to split comma-separated items into list"""
        return [item.strip() for item in self.item.split(',') if item.strip()]


class CartItem(models.Model):
    """Shopping cart items - cleared after order completion"""
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