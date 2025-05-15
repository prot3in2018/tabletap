from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db.models import Max
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import MenuItem, Order, OrderItem, Table
from collections import defaultdict
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache
from django.db import connection
from django.contrib import messages
import qrcode
import os

@never_cache
def index(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            from django.contrib.messages import get_messages
            list(get_messages(request))
            
            return redirect('dashboard')
        else:
            return render(request, 'index.html', {'error': 'Invalid credentials'})
    
    return render(request, 'index.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                return render(request, 'signup.html', {'error': 'Username already exists'})
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                login(request, user)
                return redirect('dashboard')
        else:
            return render(request, 'signup.html', {'error': 'Passwords do not match'})
    
    return render(request, 'signup.html')

@login_required
def dashboard(request):
    username = request.user.username
    return render(request, 'dashboard.html', {'username': username})

@login_required
def digital_menu(request):
    if request.method == 'POST':
        name = request.POST['item_name']
        price = request.POST['item_price']
        description = request.POST['item_description']
        category = request.POST['menu_category']
        MenuItem.objects.create(
            user=request.user,
            name=name,
            price=price,
            description=description,
            category=category
        )
        return redirect('menu')
    categories = ["Appetisers", "Soups & Salads", "Main", "Side", "Desserts", "Beverages"]
    category_items = {cat: MenuItem.objects.filter(user=request.user, category=cat) for cat in categories}
    return render(request, 'digital_menu.html', {'category_items': category_items})

@login_required
def order_management(request):
    if request.method == 'POST':
        if 'order_id' in request.POST:
            order_id = request.POST.get('order_id')
            action = request.POST.get('action')
            order = get_object_or_404(Order, id=order_id, table__user=request.user)
            if action == 'complete':
                order.status = 'Completed'
            elif action == 'cancel':
                order.status = 'Canceled'
            order.save()

        elif 'delete_all' in request.POST:
            Order.objects.filter(table__user=request.user).delete()
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='core_order'")

        return redirect('order_management')

    orders = Order.objects.filter(table__user=request.user).order_by('-timestamp')

    return render(request, 'order_management.html', {'orders': orders})

@login_required
def table_setup(request):
    if request.method == 'POST':
        try:
            table_count = int(request.POST.get('table_count'))
            if table_count <= 0:
                raise ValueError
        except (ValueError, TypeError):
            tables = Table.objects.filter(user=request.user).order_by('number')
            return render(request, 'table_setup.html', {
                'tables': tables,
                'error': "Please enter a valid number greater than 0."
            })
                    
        Table.objects.filter(user=request.user).delete()
        
        for i in range(1, table_count + 1):
            table = Table.objects.create(number=i, user=request.user)

            qr_url = f"https://tabletap.onrender.com/order/table/{request.user.id}/{table.number}/"
            qr = qrcode.make(qr_url)
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            qr_path = os.path.join(settings.MEDIA_ROOT, f"table_qr_{table.number}.png")
            qr.save(qr_path)

        return redirect('tables')
    
    tables = Table.objects.filter(user=request.user).order_by('number')
    return render(request, 'table_setup.html', {'tables': tables})

def customer_ordering(request, user_id, table_number):
    table = get_object_or_404(Table, user__id=user_id, number=table_number)
    menu_items = MenuItem.objects.filter(user=table.user).order_by('category', 'name')
    
    CATEGORY_ORDER = [
        "Appetisers",
        "Soups & Salads",
        "Main",
        "Side",
        "Desserts",
        "Beverages",
    ]
    
    grouped_items_raw = defaultdict(list)
    for item in menu_items:
        grouped_items_raw[item.category].append(item)
        
    grouped_items = {
        cat: grouped_items_raw[cat]
        for cat in CATEGORY_ORDER
        if cat in grouped_items_raw
    }
    
    if request.method == 'POST':
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
        
        latest = Order.objects.filter(table__user=table.user).aggregate(Max('user_order_number'))['user_order_number__max']
        next_order_number = latest + 1 if latest else 1

        order = Order.objects.create(
            table=table,
            session_id=session_id,
            user_order_number=next_order_number
        )
        total_quantity = 0
        for item in menu_items:
            raw_qty = request.POST.get(f'item_{item.id}', '0')
            try:
                qty = int(raw_qty)
            except ValueError:
                qty = 0

            if qty > 0:
                OrderItem.objects.create(order=order, menu_item=item, quantity=qty)
                total_quantity += qty
                
        if total_quantity == 0:
            order.delete()
            return render(request, 'customer_ordering.html', {
                'table': table,
                'grouped_items': grouped_items,
                'error': "Please select at least one item before placing your order."
            })
        return redirect('order_submitted', order_id=order.id)
    
    return render(request, 'customer_ordering.html', {
        'table': table,
        'grouped_items': grouped_items
    })


def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def delete_menu_item(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id, user=request.user)
    item.delete()
    return redirect('menu')

def order_submitted(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_submitted.html', {
        'order_id': order_id,
        'table_number': order.table.number,
        'user_id': order.table.user.id,
        'order': order
    })

def order_history(request, user_id, table_number):
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key
    table = get_object_or_404(Table, user__id=user_id, number=table_number)
    orders = Order.objects.filter(table=table, session_id=session_id).order_by('-timestamp')
    
    for order in orders:
        total = sum(item.quantity * item.menu_item.price for item in order.items.all())
        order.total_price = total
        
    return render(request, 'order_history.html', {
        'table': table,
        'orders': orders
    })

@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        
        if request.user.check_password(password):
            user = request.user
            request.user.delete()
            logout(request)
            return redirect('signup')
        else:
            return render(request, 'delete_account.html', {
                'error': "Incorrect password."
            })

    return render(request, 'delete_account.html')

@login_required
def delete_tables(request):
    if request.method == 'POST':
        tables = Table.objects.filter(user=request.user)
        for table in tables:
            qr_path = os.path.join(settings.MEDIA_ROOT, f"table_qr_{table.number}.png")
            if os.path.exists(qr_path):
                os.remove(qr_path)
        tables.delete()
    return redirect('tables')
