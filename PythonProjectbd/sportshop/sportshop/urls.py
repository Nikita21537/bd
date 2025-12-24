# sportshop/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.admin.views.decorators import staff_member_required
urlpatterns = [
    # Главная страница
    path('', views.home, name='home'),

    # Основные маршруты
    path('catalog/', views.product_list, name='catalog'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    # Поиск
    path('search/', views.search, name='search'),
    path('search/advanced/', views.advanced_search, name='advanced_search'),

    # Корзина
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('quick-add-to-cart/', views.quick_add_to_cart, name='quick_add_to_cart'),
    path('update-cart/<int:product_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Заказы
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),

    # Аутентификация
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Восстановление пароля
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='sportshop/password_reset.html'
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='sportshop/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='sportshop/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='sportshop/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # Личные кабинеты
    path('account/', views.account, name='account'),
    path('account/customer/', views.customer_account, name='customer_account'),
    path('account/profile/', views.account_profile, name='account_profile'),
    path('account/addresses/', views.account_addresses, name='account_addresses'),
    path('account/reviews/', views.account_reviews, name='account_reviews'),
    path('account/orders/', views.account_orders, name='account_orders'),

    # ПАНЕЛЬ УПРАВЛЕНИЯ - ИЗМЕНИТЕ ПУТЬ!
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),  # Было: admin/dashboard/
    path('dashboard/products/', views.admin_products, name='admin_products'),
    path('dashboard/orders/', views.admin_orders, name='admin_orders'),
    path('dashboard/users/', views.admin_users, name='admin_users'),
    path('dashboard/order-history/', views.admin_order_history, name='admin_order_history'),

    # Статические страницы
    path('about/', views.about, name='about'),
    path('contacts/', views.contacts, name='contacts'),
    path('delivery/', views.delivery_info, name='delivery'),
    path('returns/', views.return_policy, name='returns'),
    path('admin-panel/', staff_member_required(views.admin_dashboard), name='admin_panel'),
    path('admin-panel/products/', staff_member_required(views.admin_products), name='admin_products'),
    path('admin-panel/orders/', staff_member_required(views.admin_orders), name='admin_orders'),
    path('admin-panel/users/', staff_member_required(views.admin_users), name='admin_users'),
    path('api/orders/<int:order_id>/details/', views.api_order_details, name='api_order_details'),
    path('api/orders/<int:order_id>/update-status/', views.api_update_order_status, name='api_update_order_status'),
]
