"""
URL configuration for tabletap project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from core import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# urlpatterns defines the URL patterns for this system
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('menu/', views.digital_menu, name='menu'),
    path('orders/', views.order_management, name='orders'),
    path('tables/', views.table_setup, name='tables'),
    path('customer/', views.customer_ordering, name='customer'),
    path('logout/', views.logout_view, name='logout'),
    path('menu/delete/<int:item_id>/', views.delete_menu_item, name='delete_menu_item'),
    path('order/table/<int:table_number>/', views.customer_ordering, name='table_ordering'),
    path('order/table/<int:table_number>/', views.customer_ordering, name='table_ordering'),
    path('order/submitted/<int:order_id>/', views.order_submitted, name='order_submitted'),
    path('orders/', views.order_management, name='order_management'),
    path('order/history/<int:table_number>/', views.order_history, name='order_history'),
    path('account/delete/', views.delete_account, name='delete_account'),
    path('login/', auth_views.LoginView.as_view(template_name='index.html'), name='login'),
    path('tables/delete/', views.delete_tables, name='delete_tables'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
