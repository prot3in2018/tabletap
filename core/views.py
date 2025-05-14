from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import MenuItem, Order, OrderItem, Table
from collections import defaultdict
from django.views.decorators.http import require_GET
from django.db import connection
from django.contrib import messages
import qrcode
import os

# index function handles both login form submission and initial page load.
def index(request):
    # Check if the login form was submitted.
    if request.method == 'POST':
        # username and password are extracted from the form.
        username = request.POST['username']
        password = request.POST['password']
        
        # authenticate checks if the credentials are valid.
        user = authenticate(request, username=username, password=password)
        # If valid, the user is logged in and redirected to the dashboard.
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        # If login fails, show the login page again with an error message.
        else:
            return render(request, 'index.html', {'error': 'Invalid credentials'})
    
    # If the request is GET (initial page load), just render the login page.
    return render(request, 'index.html')

# signup function handles user registration and creates a new account.
def signup(request):
    # Check if the sign-up form was submitted.
    if request.method == 'POST':
        # Extract username, email, password, and confirm_password from the form.
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        # If the passwords match, attempt to create the user.
        if password == confirm_password:
            # Check if the username already exists in the database.
            if User.objects.filter(username=username).exists():
                # If username is taken, reload the form with an error message.
                return render(request, 'signup.html', {'error': 'Username already exists'})
            else:
                # Create the new user and save it to the database.
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                # Log the user in and redirect to the dashboard.
                login(request, user)
                return redirect('dashboard')
        else:
            # If passwords don't match, reload the form with an error.
            return render(request, 'signup.html', {'error': 'Passwords do not match'})
    
    # If the request is GET, show the empty sign-up form.
    return render(request, 'signup.html')

# dashboard view displays the dashboard page with the logged-in user's username.
@login_required
def dashboard(request):
    # Get the username of the currently logged-in user.
    username = request.user.username
    # Render the dashboard page with the username passed to the template.
    return render(request, 'dashboard.html', {'username': username})

# digital_menu view allows users to add new menu items and view existing ones, grouped by category.
@login_required
def digital_menu(request):
    # If the form is submitted via POST, extract the form data.
    if request.method == 'POST':
        name = request.POST['item_name']
        price = request.POST['item_price']
        description = request.POST['item_description']
        category = request.POST['menu_category']
        # Create and save a new menu item with the provided details.
        MenuItem.objects.create(
            user=request.user,
            name=name,
            price=price,
            description=description,
            category=category
        )
        # Redirect back to the menu page after adding.
        return redirect('menu')
    # Define the menu categories.
    categories = ["Appetisers", "Soups & Salads", "Main", "Side", "Desserts", "Beverages"]
    # Group the menu items by category for the current user.
    category_items = {cat: MenuItem.objects.filter(user=request.user, category=cat) for cat in categories}
    # Render the digital menu management page.
    return render(request, 'digital_menu.html', {'category_items': category_items})

# order_management view allows staff to manage, update, or clear orders.
@login_required
def order_management(request):
    # Handle form actions sent via POST.
    if request.method == 'POST':
        # Complete or cancel a specific order.
        if 'order_id' in request.POST:
            order_id = request.POST.get('order_id')
            action = request.POST.get('action')
            order = Order.objects.get(id=order_id)
            if action == 'complete':
                order.status = 'Completed'
            elif action == 'cancel':
                order.status = 'Canceled'
            order.save()
            
        # Delete all orders and reset the auto-increment counter.    
        elif 'delete_all' in request.POST:
            Order.objects.all().delete()
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='core_order'")

        return redirect('order_management')
    
    # Get all orders sorted by newest first.
    orders = Order.objects.all().order_by('-timestamp')
    # Render the order management page with order data.
    return render(request, 'order_management.html', {'orders': orders})

# table_setup view allows users to define the number of tables and generates QR codes for each one.
@login_required
def table_setup(request):
    # If the form is submitted via POST, generate QR codes.
    if request.method == 'POST':
        # Get the number of tables from the form.
        table_count = int(request.POST.get('table_count'))
        # Delete any existing tables for this user.
        Table.objects.filter(user=request.user).delete()
        
        # Create tables and generate a QR code for each.
        for i in range(1, table_count + 1):
            table = Table.objects.create(number=i, user=request.user)

            qr_url = f"https://tabletap.onrender.com/order/table/{table.number}/"
            qr = qrcode.make(qr_url)
            qr_path = os.path.join(settings.MEDIA_ROOT, f"table_qr_{table.number}.png")
            qr.save(qr_path)

        return redirect('tables')
    
    # Get all tables created by the current user.
    tables = Table.objects.filter(user=request.user).order_by('number')
    return render(request, 'table_setup.html', {'tables': tables})

# customer_ordering view allows customers to place orders by scanning a table-specific QR code.
def customer_ordering(request, table_number):
    # Get the Table object using the table number in the URL, or return 404 if not found.
    table = get_object_or_404(Table, number=table_number)
    # Retrieve all menu items created by the table's owner, sorted by category and name.
    menu_items = MenuItem.objects.filter(user=table.user).order_by('category', 'name')
    
    # Define the order in which categories should be displayed on the page.
    CATEGORY_ORDER = [
        "Appetisers",
        "Soups & Salads",
        "Main",
        "Side",
        "Desserts",
        "Beverages",
    ]
    
    # Group menu items by their category using a temporary dictionary.
    grouped_items_raw = defaultdict(list)
    for item in menu_items:
        grouped_items_raw[item.category].append(item)
        
    # Reorder grouped items to match CATEGORY_ORDER for consistent display.
    grouped_items = {
        cat: grouped_items_raw[cat]
        for cat in CATEGORY_ORDER
        if cat in grouped_items_raw
    }
    
    # If the customer submits the form:
    if request.method == 'POST':
        # Create a session if one doesn't exist yet.
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
        
        # Create a new Order object linked to the current table and session.
        order = Order.objects.create(table=table, session_id=session_id)
        total_quantity = 0
        
        # Loop through all menu items and check if the customer selected a quantity > 0.
        for item in menu_items:
            raw_qty = request.POST.get(f'item_{item.id}', '0')
            try:
                qty = int(raw_qty)
            except ValueError:
                qty = 0

            if qty > 0:
                # Create an OrderItem record for each item with quantity > 0.
                OrderItem.objects.create(order=order, menu_item=item, quantity=qty)
                total_quantity += qty
                
        # If no items were selected, delete the empty order and show an error message.
        if total_quantity == 0:
            order.delete()
            return render(request, 'customer_ordering.html', {
                'table': table,
                'grouped_items': grouped_items,
                'error': "Please select at least one item before placing your order."
            })
        # If valid items were selected, redirect to the order confirmation page.
        return redirect('order_submitted', order_id=order.id)
    
    # If the page is accessed via GET, just render the ordering form.
    return render(request, 'customer_ordering.html', {
        'table': table,
        'grouped_items': grouped_items
    })


# logout_view logs the user out and redirects to the login page.
def logout_view(request):
    logout(request)
    return redirect('index')

# delete_menu_item allows a user to delete one of their own menu items.
@login_required
def delete_menu_item(request, item_id):
    # Ensure the item belongs to the logged-in user.
    item = get_object_or_404(MenuItem, id=item_id, user=request.user)
    # Delete the menu item.
    item.delete()
    return redirect('menu')

# order_submitted displays a confirmation message after a customer places an order.
def order_submitted(request, order_id):
    # Get the order and related table number.
    order = get_object_or_404(Order, id=order_id)
    table_number = order.table.number
    # Show confirmation with order ID and table number.
    return render(request, 'order_submitted.html', {
        'order_id': order_id,
        'table_number': table_number
    })

# order_history shows all past orders by session ID for a specific table.
def order_history(request, table_number):
    # Ensure the session exists.
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key
    # Find the table and retrieve orders by session.
    table = get_object_or_404(Table, number=table_number)
    orders = Order.objects.filter(table=table, session_id=session_id).order_by('-timestamp')
    
    # Calculate the total price for each order.
    for order in orders:
        total = sum(item.quantity * item.menu_item.price for item in order.items.all())
        order.total_price = total
        
    return render(request, 'order_history.html', {
        'table': table,
        'orders': orders
    })

# delete_account allows users to delete their account after confirming their password.
@login_required
def delete_account(request):
    # If the form is submitted:
    if request.method == 'POST':
        password = request.POST.get('password')
        
        # If the password is correct, delete the user and log out.
        if request.user.check_password(password):
            user = request.user
            request.user.delete()
            logout(request)
            messages.success(request, "Your account has been deleted.")
            return redirect('signup')
        else:
            # Show an error message if the password is incorrect.
            messages.error(request, "Incorrect password.")

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
        messages.success(request, "All tables and QR codes deleted.")
    return redirect('tables')
