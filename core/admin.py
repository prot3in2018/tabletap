from django.contrib import admin
from .models import MenuItem, Table, Order, OrderItem

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'user')
    search_fields = ('name', 'category')
    list_filter = ('category', 'user')
    ordering = ('category', 'name')

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'user')
    list_filter = ('user',)
    ordering = ('user', 'number')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'quantity')
    list_filter = ('menu_item',)
    search_fields = ('menu_item__name',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table', 'timestamp', 'status', 'user_order_number')
    list_filter = ('status', 'timestamp', 'table')
    ordering = ('-timestamp',)
    inlines = [OrderItemInline]
