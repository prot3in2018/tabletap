from django.db import models
from django.contrib.auth.models import User

# MenuItem model represents an item on the restaurant menu.
# CATEGORY_CHOICES defines a list of category options as tuples (values, display name).
# user links each item to a specific user. If the user delete an account, their associated items are also deleted.
# name stores the menu item's name.
# price stores the price of menu item.
# description stores the description of menu item.
# category stores the category of menu item. It limits the category to one of the predefined choices from CATEGORY_CHOICES.
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
    
    # __str__ returns the name of the object, otherwise <MenuItem object (1)> appears.
    def __str__(self):
        return self.name

# Table model represents a restaurant table in the system.
# number stores the unique table number.
# user associates each table with a specific user. If the user delete an account, their tables are deleted as well.
class Table(models.Model):
    number = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'number')
    
    # __str__ returns the table number, otherwise <Table object (1)> appears.
    def __str__(self):
        return f"Table {self.number}"

# Order model represents a customer's order in the system.
# table connects the order to a specific table. If the table is deleted, its orders are also deleted.
# session_id tracks a customer's order session.
# timestamp records the data and time when the order is created.
# status stores the order's status.
class Order(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Canceled', 'Canceled')
    ], default='Pending')
    
    # __str__ returns the order ID and the table number, otherwise <Order object (x)> appears.
    def __str__(self):
        return f"Order {self.id} (Table {self.table.number})"

# OrderItem model represents a specific menu item and its quantity within a customer's order.
# order connects each OrderItem to a specific Order. If the order is deleted, its associated items are deleted as well.
# menu_item connects to the specific menu item being ordered. If the menu item is deleted, the related order item is deleted as well.
# quantity indicates how many units of the menu item were ordered.
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    
    # __str__ returns the quantity and the menu item, otherwise <OrderItem object (x)> appears.
    def __str__(self):
        return f"{self.quantity} × {self.menu_item.name}"
