# shop/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal
import json

from .models import *
from .forms import *
from .decorators import *


def index(request):
    """Главная страница с каталогом товаров"""
    products = Product.objects.filter(is_active=True)

    # Фильтрация
    category_id = request.GET.get('category')
    manufacturer_id = request.GET.get('manufacturer')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    search_query = request.GET.get('q')

    if category_id:
        products = products.filter(category_id=category_id)
    if manufacturer_id:
        products = products.filter(manufacturer_id=manufacturer_id)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(sku__icontains=search_query)
        )

    categories = Category.objects.all()
    manufacturers = Manufacturer.objects.all()

    context = {
        'products': products,
        'categories': categories,
        'manufacturers': manufacturers,
        'search_query': search_query,
    }
    return render(request, 'shop/index.html', context)


def product_detail(request, product_id):
    """Детальная страница товара"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    reviews = Review.objects.filter(product=product, is_approved=True)

    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            messages.success(request, 'Ваш отзыв отправлен на модерацию')
            return redirect('product_detail', product_id=product_id)
    else:
        form = ReviewForm()

    context = {
        'product': product,
        'reviews': reviews,
        'form': form,
    }
    return render(request, 'shop/product_detail.html', context)


@login_required
def cart_view(request):
    """Корзина пользователя"""
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.total_price for item in cart_items)

    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'shop/cart.html', context)


@require_POST
@login_required
def add_to_cart(request, product_id):
    """Добавление товара в корзину"""
    product = get_object_or_404(Product, id=product_id, is_active=True)

    if product.stock_quantity <= 0:
        return JsonResponse({'error': 'Товар отсутствует на складе'}, status=400)

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': 1}
    )

    if not created:
        if cart_item.quantity < product.stock_quantity:
            cart_item.quantity += 1
            cart_item.save()
        else:
            return JsonResponse({'error': 'Недостаточно товара на складе'}, status=400)

    return JsonResponse({
        'success': True,
        'message': 'Товар добавлен в корзину',
        'cart_count': CartItem.objects.filter(user=request.user).count()
    })


@require_POST
@login_required
def remove_from_cart(request, item_id):
    """Удаление товара из корзины"""
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()

    messages.success(request, 'Товар удален из корзины')
    return redirect('cart')


@login_required
def checkout(request):
    """Оформление заказа"""
    cart_items = CartItem.objects.filter(user=request.user)

    if not cart_items:
        messages.warning(request, 'Ваша корзина пуста')
        return redirect('cart')

    # Проверка наличия товаров
    for item in cart_items:
        if item.quantity > item.product.stock_quantity:
            messages.error(request, f'Товар "{item.product.name}" недоступен в нужном количестве')
            return redirect('cart')

    total = sum(item.total_price for item in cart_items)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Создание заказа
            order = Order(
                user=request.user,
                total_amount=total,
                shipping_address=form.cleaned_data['shipping_address'],
                billing_address=form.cleaned_data.get('billing_address', ''),
            )
            order.save()

            # Создание позиций заказа и обновление количества на складе
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.product.price,
                    total_price=cart_item.total_price
                )

                # Уменьшение количества на складе
                cart_item.product.stock_quantity -= cart_item.quantity
                cart_item.product.save()

            # Очистка корзины
            cart_items.delete()

            # Логирование
            SystemLog.objects.create(
                user=request.user,
                action='CREATE_ORDER',
                description=f'Создан заказ {order.order_number} на сумму {total} руб.',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            messages.success(request, f'Заказ #{order.order_number} успешно оформлен!')
            return redirect('order_detail', order_id=order.id)
    else:
        initial_data = {
            'shipping_address': request.user.address,
        }
        form = OrderForm(initial=initial_data)

    context = {
        'cart_items': cart_items,
        'total': total,
        'form': form,
    }
    return render(request, 'shop/checkout.html', context)


@login_required
def profile(request):
    """Личный кабинет пользователя"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'orders': orders,
    }
    return render(request, 'shop/profile.html', context)


@login_required
def order_detail(request, order_id):
    """Детальная информация о заказе"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    context = {
        'order': order,
    }
    return render(request, 'shop/order_detail.html', context)


# ========== АДМИН-ПАНЕЛЬ ==========

@login_required
@manager_required
def admin_dashboard(request):
    """Панель управления для менеджеров и администраторов"""
    stats = {
        'total_orders': Order.objects.count(),
        'total_products': Product.objects.filter(is_active=True).count(),
        'total_users': User.objects.count(),
        'pending_orders': Order.objects.filter(status='Новый').count(),
    }

    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    low_stock_products = Product.objects.filter(stock_quantity__lt=10, is_active=True)[:10]

    context = {
        'stats': stats,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'shop/admin/dashboard.html', context)


@login_required
@manager_required
def admin_order_list(request):
    """Список заказов для управления"""
    orders = Order.objects.all().order_by('-created_at')

    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)

    context = {
        'orders': orders,
    }
    return render(request, 'shop/admin/order_list.html', context)


@login_required
@manager_required
def admin_order_update(request, order_id):
    """Изменение статуса заказа"""
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            old_status = order.status
            order.status = new_status
            order.save()

            # Логирование
            SystemLog.objects.create(
                user=request.user,
                action='UPDATE_ORDER',
                description=f'Изменен статус заказа {order.order_number}: {old_status} -> {new_status}',
                ip_address=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, f'Статус заказа #{order.order_number} изменен на "{new_status}"')

    return redirect('admin_order_list')


@login_required
@admin_required
def admin_user_list(request):
    """Управление пользователями (только для администраторов)"""
    users = User.objects.all().order_by('-created_at')

    context = {
        'users': users,
    }
    return render(request, 'shop/admin/user_list.html', context)


# ========== АУТЕНТИФИКАЦИЯ ==========

def login_view(request):
    """Вход в систему"""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)

            # Логирование
            SystemLog.objects.create(
                user=user,
                action='LOGIN',
                description='Успешный вход в систему',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
        else:
            messages.error(request, 'Неверный email или пароль')

    return render(request, 'shop/login.html')


def register_view(request):
    """Регистрация нового пользователя"""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Логирование
            SystemLog.objects.create(
                user=user,
                action='USER_REGISTER',
                description='Новый пользователь зарегистрирован',
                ip_address=request.META.get('REMOTE_ADDR')
            )

            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('index')
    else:
        form = UserRegistrationForm()

    context = {'form': form}
    return render(request, 'shop/register.html', context)


@login_required
def logout_view(request):
    """Выход из системы"""
    # Логирование
    SystemLog.objects.create(
        user=request.user,
        action='LOGOUT',
        description='Выход из системы',
        ip_address=request.META.get('REMOTE_ADDR')
    )

    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('index')