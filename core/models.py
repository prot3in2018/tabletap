from django.db import models
from django.contrib.auth.models import User

class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ('Appetisers', 'Appetisers'),
        ('Soups & Salads', 'Soups & Salads'),
        ('Main', 'Main'),
        ('Side', 'Side'),
        ('Desserts', 'Desserts'),
        ('Beverages', 'Beverages'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Main')
    
    def __str__(self):
        return self.name

class Table(models.Model):
    number = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'number')

    def __str__(self):
        return f"Table {self.number}"

class Order(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user_order_number = models.PositiveIntegerField(null=True)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Canceled', 'Canceled')
    ], default='Pending')
    
    def __str__(self):
        return f"Order {self.id} (Table {self.table.number})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    
    def __str__(self):
        return f"{self.quantity} × {self.menu_item.name}"
