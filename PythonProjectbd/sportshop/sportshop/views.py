# sportshop/views.py
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import json
import uuid

from .models import Product, Category, Order, OrderItem, Review, UserProfile, Address, Cart, CartItem
from .permissions import customer_required, manager_required, admin_required


# ==================== ГЛАВНАЯ СТРАНИЦА ====================
def home(request):
    """Главная страница с приветствием пользователя"""
    try:
        # Получаем товары для разных секций
        featured_products = Product.objects.filter(
            in_stock=True,
            is_active=True
        ).order_by('-rating', '-created_at')[:8]

        discounted_products = Product.objects.filter(
            discount_price__isnull=False,
            in_stock=True,
            is_active=True
        ).order_by('?')[:6]

        # Новинки
        new_products = Product.objects.filter(
            in_stock=True,
            is_active=True,
            created_at__gte=timezone.now() - timezone.timedelta(days=30)
        )[:6]

        # Категории с товарами
        categories = Category.objects.annotate(
            product_count=Count('products')
        ).filter(product_count__gt=0)[:6]

        # Данные для приветствия пользователя
        context = {
            'featured_products': featured_products,
            'discounted_products': discounted_products,
            'new_products': new_products,
            'categories': categories,
        }

        # Если пользователь авторизован, добавляем его данные
        if request.user.is_authenticated:
            # Получаем профиль пользователя
            profile, created = UserProfile.objects.get_or_create(user=request.user)

            # Получаем заказы пользователя
            orders_count = Order.objects.filter(user=request.user).count()

            # Получаем корзину
            cart = Cart.objects.filter(user=request.user).first()
            cart_count = cart.get_total_quantity() if cart else 0

            # Получаем группы пользователя
            user_groups = request.user.groups.values_list('name', flat=True)

            context.update({
                'orders_count': orders_count,
                'bonus_points': profile.bonus_points,
                'cart_count': cart_count,
                'user_groups': user_groups,
            })

        return render(request, 'sportshop/index.html', context)

    except Exception as e:
        print(f"Ошибка на главной странице: {e}")
        context = {
            'featured_products': [],
            'discounted_products': [],
            'new_products': [],
            'categories': [],
        }

        if request.user.is_authenticated:
            user_groups = request.user.groups.values_list('name', flat=True)
            context.update({
                'orders_count': 0,
                'bonus_points': 0,
                'cart_count': 0,
                'user_groups': user_groups,
            })

        return render(request, 'sportshop/index.html', context)


# ==================== КОНТЕКСТНЫЙ ПОИСК ====================
def search(request):
    """
    Контекстный поиск (полнотекстовый) по названию и описанию товаров
    """
    query = request.GET.get('q', '').strip()

    products = Product.objects.filter(in_stock=True, is_active=True)

    if query:
        # Разбиваем запрос на слова для более точного поиска
        words = query.split()

        # Создаем Q-объект для каждого слова
        q_objects = Q()
        for word in words:
            q_objects |= Q(name__icontains=word) | Q(description__icontains=word)

        products = products.filter(q_objects)

        # Если ничего не найдено, ищем по категориям и брендам
        if not products.exists():
            products = Product.objects.filter(
                Q(category__name__icontains=query) |
                Q(brand__icontains=query)
            ).filter(in_stock=True, is_active=True)
    else:
        products = Product.objects.none()

    # Сортировка по релевантности
    products = products.order_by('-rating', '-created_at')

    # Пагинация
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'query': query,
        'products': page_obj,
        'results_count': products.count(),
        'search_type': 'contextual',
    }
    return render(request, 'sportshop/search_results.html', context)


# ==================== АТРИБУТНЫЙ ПОИСК ====================
def advanced_search(request):
    """
    Атрибутный поиск (с фильтрами) - отдельная страница расширенного поиска
    """
    products = Product.objects.filter(in_stock=True, is_active=True)

    # Инициализируем фильтры
    filters = {}
    has_filters = False

    # Фильтр по текстовому запросу
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__icontains=query)
        )
        filters['q'] = query
        has_filters = True

    # Фильтр по категории
    category_id = request.GET.get('category')
    if category_id and category_id != 'all':
        products = products.filter(category_id=category_id)
        filters['category'] = category_id
        has_filters = True

    # Фильтр по цене
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    if price_min and price_min.isdigit():
        products = products.filter(price__gte=int(price_min))
        filters['price_min'] = price_min
        has_filters = True
    if price_max and price_max.isdigit():
        products = products.filter(price__lte=int(price_max))
        filters['price_max'] = price_max
        has_filters = True

    # Фильтр по бренду
    brand = request.GET.get('brand')
    if brand and brand != 'all':
        products = products.filter(brand__iexact=brand)
        filters['brand'] = brand
        has_filters = True

    # Фильтр по наличию
    in_stock_only = request.GET.get('in_stock', 'true')
    if in_stock_only == 'true':
        products = products.filter(in_stock=True)
        filters['in_stock'] = 'true'
        has_filters = True

    # Фильтр по скидкам
    has_discount = request.GET.get('has_discount')
    if has_discount == 'true':
        products = products.filter(discount_price__isnull=False)
        filters['has_discount'] = 'true'
        has_filters = True

    # Сортировка
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-rating', '-views')
    elif sort_by == 'popular':
        products = products.order_by('-views', '-rating')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-created_at')
    filters['sort'] = sort_by

    # Пагинация
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Получаем данные для фильтров
    categories = Category.objects.all()
    brands = Product.objects.filter(
        in_stock=True,
        is_active=True
    ).exclude(brand='').values_list('brand', flat=True).distinct()

    context = {
        'products': page_obj,
        'categories': categories,
        'brands': brands,
        'filters': filters,
        'has_filters': has_filters,
        'results_count': products.count(),
        'search_type': 'advanced',
    }
    return render(request, 'sportshop/advanced_search.html', context)


# ==================== КАТАЛОГ ТОВАРОВ ====================
def product_list(request):
    """Страница каталога товаров"""
    products = Product.objects.filter(in_stock=True, is_active=True)
    categories = Category.objects.annotate(product_count=Count('products')).filter(product_count__gt=0)

    # Фильтрация по поисковому запросу
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Фильтрация по категории
    category_id = request.GET.get('category')
    if category_id and category_id != 'all':
        products = products.filter(category_id=category_id)

    # Фильтрация по цене
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price and min_price.isdigit():
        products = products.filter(price__gte=int(min_price))
    if max_price and max_price.isdigit():
        products = products.filter(price__lte=int(max_price))

    # Сортировка
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == '-name':
        products = products.order_by('-name')
    elif sort_by == 'price':
        products = products.order_by('price')
    elif sort_by == '-price':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    elif sort_by == 'popular':
        products = products.order_by('-views')
    else:
        products = products.order_by('-created_at')

    # Пагинация
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'categories': categories,
        'total_products': products.count(),
        'sort_by': sort_by,
    }
    return render(request, 'sportshop/catalog.html', context)


# ==================== ДЕТАЛЬНАЯ СТРАНИЦА ТОВАРА ====================
def product_detail(request, product_id):
    """Детальная страница товара"""
    product = get_object_or_404(Product, id=product_id, is_active=True)

    # Похожие товары (той же категории)
    similar_products = Product.objects.filter(
        category=product.category,
        in_stock=True,
        is_active=True
    ).exclude(id=product_id)[:4]

    # Отзывы к товару
    reviews = Review.objects.filter(
        product=product,
        is_published=True
    ).order_by('-created_at')

    # Увеличиваем счетчик просмотров
    product.views += 1
    product.save(update_fields=['views'])

    context = {
        'product': product,
        'similar_products': similar_products,
        'reviews': reviews,
        'reviews_count': reviews.count(),
        'average_rating': reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0,
    }
    return render(request, 'sportshop/product_detail.html', context)


# ==================== БЫСТРОЕ ДОБАВЛЕНИЕ В КОРЗИНУ ====================
@require_POST
@login_required
def quick_add_to_cart(request):
    """
    Быстрое добавление в корзину с главной страницы (без указания количества)
    """
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')

        product = get_object_or_404(Product, id=product_id)

        # Проверяем наличие товара
        if not product.in_stock or product.stock_quantity <= 0:
            return JsonResponse({
                'success': False,
                'message': f'Товар "{product.name}" отсутствует на складе'
            })

        cart, created = Cart.objects.get_or_create(user=request.user)

        # Проверяем, есть ли уже товар в корзине
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        # Возвращаем JSON для AJAX
        return JsonResponse({
            'success': True,
            'cart_count': cart.get_total_quantity(),
            'message': f'Товар "{product.name}" добавлен в корзину',
            'product_name': product.name,
            'product_price': float(product.get_final_price()),
            'cart_total': float(cart.get_total_price()),
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# ==================== КОРЗИНА ====================
@customer_required
def cart_view(request):
    """Просмотр корзины"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product').all()

    # Расчет итогов
    subtotal = sum(item.get_total_price() for item in cart_items)
    delivery_cost = 0  # Базовая стоимость доставки
    grand_total = subtotal + delivery_cost

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'cart_total_quantity': cart.get_total_quantity(),
        'cart_subtotal': subtotal,
        'cart_discount': 0,
        'cart_grand_total': grand_total,
        'delivery_cost': delivery_cost,
    }
    return render(request, 'sportshop/cart.html', context)


@require_POST
@customer_required
def add_to_cart(request, product_id):
    """Добавление товара в корзину (AJAX)"""
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
    except:
        quantity = 1

    # Проверяем наличие
    if not product.in_stock or product.stock_quantity < quantity:
        return JsonResponse({
            'success': False,
            'message': f'Недостаточно товара "{product.name}" на складе'
        })

    # Проверяем, есть ли уже товар в корзине
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    # Возвращаем JSON для AJAX
    return JsonResponse({
        'success': True,
        'cart_count': cart.get_total_quantity(),
        'item_total': cart_item.get_total_price(),
        'cart_subtotal': cart.get_total_price(),
        'message': f'Товар "{product.name}" добавлен в корзину'
    })


@require_POST
@customer_required
def update_cart_item(request, product_id):
    """Обновление количества товара в корзине (AJAX)"""
    product = get_object_or_404(Product, id=product_id)
    cart = get_object_or_404(Cart, user=request.user)

    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
    except:
        return JsonResponse({'success': False, 'error': 'Неверный формат данных'})

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)

        # Проверяем наличие на складе
        if quantity > product.stock_quantity:
            return JsonResponse({
                'success': False,
                'error': f'На складе только {product.stock_quantity} шт.'
            })

        if quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.save()
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Товар не найден в корзине'})

    return JsonResponse({
        'success': True,
        'cart_count': cart.get_total_quantity(),
        'item_total': cart_item.get_total_price() if quantity > 0 else 0,
        'cart_subtotal': cart.get_total_price(),
    })


@require_POST
@customer_required
def remove_from_cart(request, product_id):
    """Удаление товара из корзины (AJAX)"""
    product = get_object_or_404(Product, id=product_id)
    cart = get_object_or_404(Cart, user=request.user)

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.delete()
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Товар не найден в корзине'})

    return JsonResponse({
        'success': True,
        'cart_count': cart.get_total_quantity(),
        'cart_subtotal': cart.get_total_price(),
    })


# ==================== ЛИЧНЫЕ КАБИНЕТЫ ====================
@login_required
def account(request):
    """Перенаправление на соответствующий личный кабинет"""
    print(f"DEBUG ACCOUNT VIEW: User = {request.user.username}")
    print(f"DEBUG ACCOUNT VIEW: Groups = {list(request.user.groups.values_list('name', flat=True))}")

    # Жесткая проверка для admin_ordinary
    if request.user.username == 'admin_ordinary':
        print("DEBUG: Hard redirect for admin_ordinary to admin_dashboard")
        return redirect('admin_dashboard')

    # Проверяем права
    user = request.user

    # Суперпользователь всегда идет в админку
    if user.is_superuser:
        print("DEBUG: Superuser -> admin_dashboard")
        return redirect('admin_dashboard')

    # Проверяем группы пользователя
    user_groups = list(user.groups.values_list('name', flat=True))

    # Если пользователь в группах administrator или manager
    if 'administrator' in user_groups or 'manager' in user_groups:
        print(f"DEBUG: User in admin/manager groups -> admin_dashboard")
        return redirect('admin_dashboard')

    # Все остальные (customer или нет группы) идут в личный кабинет
    print(f"DEBUG: Regular user -> customer_account")
    return redirect('customer_account')

@customer_required
def customer_account(request):
    """Личный кабинет покупателя"""
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    # Статистика пользователя
    orders = Order.objects.filter(user=user)
    total_orders = orders.count()
    total_spent = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    active_orders = orders.filter(status__in=['pending', 'processing', 'shipped']).count()

    # Последние заказы
    recent_orders = orders.order_by('-created_at')[:5]

    # Адреса доставки
    addresses = Address.objects.filter(user=user).order_by('-is_default', '-created_at')[:3]

    # Последние отзывы
    recent_reviews = Review.objects.filter(user=user).order_by('-created_at')[:3]

    context = {
        'user': user,
        'profile': profile,
        'orders_count': total_orders,
        'total_spent': total_spent,
        'active_orders_count': active_orders,
        'recent_orders': recent_orders,
        'addresses': addresses,
        'recent_reviews': recent_reviews,
        'bonus_points': profile.bonus_points,
        'section': 'dashboard',
    }
    return render(request, 'sportshop/customer_dashboard.html', context)


@customer_required
def account_orders(request):
    """Страница заказов пользователя"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Пагинация
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'total_orders': orders.count(),
        'section': 'orders',
    }
    return render(request, 'sportshop/customer_orders.html', context)


@customer_required
def account_profile(request):
    """Редактирование профиля"""
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        # Обновление данных пользователя
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()

        # Обновление профиля
        profile.phone = request.POST.get('phone', '')
        if request.POST.get('birth_date'):
            profile.birth_date = request.POST.get('birth_date')
        profile.save()

        messages.success(request, 'Профиль успешно обновлен!')
        return redirect('account_profile')

    context = {
        'profile': profile,
        'section': 'profile',
    }
    return render(request, 'sportshop/customer_profil.html', context)


@customer_required
def account_addresses(request):
    """Управление адресами доставки"""
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')

    if request.method == 'POST':
        address_id = request.POST.get('address_id')

        if address_id:  # Редактирование существующего адреса
            address = get_object_or_404(Address, id=address_id, user=request.user)
            action = request.POST.get('action')

            if action == 'delete':
                address.delete()
                messages.success(request, 'Адрес удален')
            elif action == 'set_default':
                # Снимаем флаг default со всех адресов
                Address.objects.filter(user=request.user).update(is_default=False)
                address.is_default = True
                address.save()
                messages.success(request, 'Адрес установлен как основной')
            else:
                # Обновление данных адреса
                address.name = request.POST.get('name')
                address.city = request.POST.get('city')
                address.street = request.POST.get('street')
                address.postal_code = request.POST.get('postal_code')
                address.phone = request.POST.get('phone')
                address.is_default = request.POST.get('is_default') == 'on'
                address.save()
                messages.success(request, 'Адрес обновлен')
        else:  # Создание нового адреса
            address = Address.objects.create(
                user=request.user,
                name=request.POST.get('name'),
                city=request.POST.get('city'),
                street=request.POST.get('street'),
                postal_code=request.POST.get('postal_code'),
                phone=request.POST.get('phone'),
                is_default=request.POST.get('is_default') == 'on'
            )

            # Если установлен как основной, снимаем флаг с других
            if address.is_default:
                Address.objects.filter(user=request.user).exclude(id=address.id).update(is_default=False)

            messages.success(request, 'Адрес добавлен')

        return redirect('account_addresses')

    context = {
        'addresses': addresses,
        'section': 'addresses',
    }
    return render(request, 'sportshop/customer_addresses.html', context)


@customer_required
def account_reviews(request):
    """Отзывы пользователя"""
    reviews = Review.objects.filter(user=request.user).order_by('-created_at')

    if request.method == 'POST':
        review_id = request.POST.get('review_id')
        action = request.POST.get('action')

        if action == 'delete':
            review = get_object_or_404(Review, id=review_id, user=request.user)
            review.delete()
            messages.success(request, 'Отзыв удален')
            return redirect('account_reviews')

    context = {
        'reviews': reviews,
        'section': 'reviews',
    }
    return render(request, 'sportshop/customer_reviews.html', context)


# ==================== АДМИН-ПАНЕЛЬ ====================
@manager_required  # или @admin_required, но лучше @manager_required
def admin_dashboard(request):
    """Дашборд администратора"""
    print(f"DEBUG ADMIN DASHBOARD: User {request.user.username} accessing dashboard")

    # Статистика
    today = timezone.now().date()

    stats = {
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'total_users': User.objects.count(),
        'total_products': Product.objects.count(),
        'revenue': Order.objects.filter(status='delivered').aggregate(total=Sum('total_amount'))['total'] or 0,
        'today_orders': Order.objects.filter(created_at__date=today).count(),
        'weekly_revenue': Order.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7),
            status='delivered'
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
    }

    # Последние заказы
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]

    # Популярные товары
    popular_products = Product.objects.filter(in_stock=True).order_by('-views', '-rating')[:5]

    # Новые пользователи
    new_users = User.objects.order_by('-date_joined')[:5]

    # Группы пользователя
    user_groups = request.user.groups.values_list('name', flat=True)

    context = {
        'stats': stats,
        'recent_orders': recent_orders,
        'popular_products': popular_products,
        'new_users': new_users,
        'user_groups': user_groups,
        'section': 'dashboard',
    }

    # ВАЖНО: Убедитесь, что рендерится правильный шаблон
    print(f"DEBUG: Rendering admin_dashboard.html")
    return render(request, 'sportshop/admin_dashboard.html', context)


@manager_required
def admin_products(request):
    """Управление товарами (для менеджеров и администраторов)"""
    products = Product.objects.all().order_by('-created_at')

    # Фильтрация
    category_id = request.GET.get('category')
    if category_id and category_id != 'all':
        products = products.filter(category_id=category_id)

    in_stock = request.GET.get('in_stock')
    if in_stock == 'true':
        products = products.filter(in_stock=True)
    elif in_stock == 'false':
        products = products.filter(in_stock=False)

    # Поиск
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(description__icontains=query)
        )

    # Пагинация
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    # Группы пользователя
    user_groups = request.user.groups.values_list('name', flat=True)

    context = {
        'products': page_obj,
        'categories': categories,
        'total_products': products.count(),
        'user_groups': user_groups,
        'section': 'products',
    }
    return render(request, 'sportshop/products.html', context)


@manager_required
def admin_orders(request):
    """Управление заказами (для менеджеров и администраторов)"""
    orders = Order.objects.select_related('user').prefetch_related('items').all()

    # Фильтрация по статусу
    status = request.GET.get('status')
    if status and status != 'all':
        orders = orders.filter(status=status)

    # Поиск
    query = request.GET.get('q')
    if query:
        orders = orders.filter(
            Q(order_number__icontains=query) |
            Q(user__username__icontains=query) |
            Q(recipient_name__icontains=query)
        )

    # Счетчики для фильтров
    status_counts = {
        'pending': Order.objects.filter(status='pending').count(),
        'processing': Order.objects.filter(status='processing').count(),
        'delivered': Order.objects.filter(status='delivered').count(),
    }

    # Сортировка
    orders = orders.order_by('-created_at')

    # Пагинация
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Группы пользователя
    user_groups = request.user.groups.values_list('name', flat=True)

    context = {
        'orders': page_obj,
        'total_orders': orders.count(),
        'pending_count': status_counts['pending'],
        'processing_count': status_counts['processing'],
        'delivered_count': status_counts['delivered'],
        'status_choices': Order.STATUS_CHOICES,
        'user_groups': user_groups,
        'section': 'orders',
    }
    return render(request, 'sportshop/orders.html', context)


@admin_required
def admin_users(request):
    """Управление пользователями (только для администраторов)"""
    from django.contrib.auth.models import User, Group

    users = User.objects.all().order_by('-date_joined')

    # Фильтрация по группе
    group_id = request.GET.get('group')
    if group_id and group_id != 'all':
        users = users.filter(groups__id=group_id)

    # Фильтрация по активности
    is_active = request.GET.get('is_active')
    if is_active == 'true':
        users = users.filter(is_active=True)
    elif is_active == 'false':
        users = users.filter(is_active=False)

    # Поиск
    query = request.GET.get('q')
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    # Пагинация
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    groups = Group.objects.all()

    # Группы пользователя
    user_groups = request.user.groups.values_list('name', flat=True)

    context = {
        'users': page_obj,
        'groups': groups,
        'total_users': users.count(),
        'user_groups': user_groups,
        'section': 'users',
    }
    return render(request, 'sportshop/users.html', context)


@manager_required
def admin_order_history(request):
    """История всех заказов (для администраторов и менеджеров)"""
    # Получаем все заказы
    orders = Order.objects.select_related('user').prefetch_related('items').all()

    # Фильтрация по дате
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status', 'all')
    user_id = request.GET.get('user_id')

    if start_date:
        orders = orders.filter(created_at__gte=start_date)
    if end_date:
        orders = orders.filter(created_at__lte=end_date)
    if status and status != 'all':
        orders = orders.filter(status=status)
    if user_id and user_id != 'all':
        orders = orders.filter(user_id=user_id)

    # Сортировка по дате (сначала новые)
    orders = orders.order_by('-created_at')

    # Статистика
    stats = {
        'total_orders': orders.count(),
        'total_amount': orders.aggregate(total=Sum('total_amount'))['total'] or 0,
        'pending_orders': orders.filter(status='pending').count(),
        'completed_orders': orders.filter(status='delivered').count(),
    }

    # Пагинация
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Все пользователи для фильтра
    users = User.objects.all().order_by('username')

    # Группы пользователя
    user_groups = request.user.groups.values_list('name', flat=True)

    context = {
        'orders': page_obj,
        'stats': stats,
        'users': users,
        'status_choices': Order.STATUS_CHOICES,
        'user_groups': user_groups,
        'section': 'order_history',
    }
    return render(request, 'sportshop/order_history.html', context)


@manager_required
def admin_products(request):
    """Управление товарами (для менеджеров и администраторов)"""
    products = Product.objects.all().order_by('-created_at')

    # Фильтрация
    category_id = request.GET.get('category')
    if category_id and category_id != 'all':
        products = products.filter(category_id=category_id)

    in_stock = request.GET.get('in_stock')
    if in_stock == 'true':
        products = products.filter(in_stock=True)
    elif in_stock == 'false':
        products = products.filter(in_stock=False)

    # Поиск
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(description__icontains=query)
        )

    # Проверяем, может ли пользователь удалять товары
    can_delete = request.user.is_superuser or request.user.groups.filter(name='administrator').exists()

    # Пагинация
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    # Группы пользователя
    user_groups = request.user.groups.values_list('name', flat=True)

    context = {
        'products': page_obj,
        'categories': categories,
        'total_products': products.count(),
        'user_groups': user_groups,
        'can_delete': can_delete,  # Передаем в шаблон
        'section': 'products',
    }
    return render(request, 'sportshop/products.html', context)


# ==================== ЗАКАЗЫ ====================
@customer_required
def checkout(request):
    """Страница оформления заказа"""
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all()

    if not cart_items:
        messages.warning(request, 'Ваша корзина пуста')
        return redirect('cart')

    # Получаем адреса пользователя
    addresses = Address.objects.filter(user=request.user).order_by('-is_default')

    # Расчет стоимости
    subtotal = cart.get_total_price()
    delivery_method = request.GET.get('delivery', 'pickup')

    # Стоимость доставки в зависимости от метода
    delivery_costs = {
        'pickup': 0,
        'courier': 300,
        'post': 250,
        'cdek': 350,
    }
    delivery_cost = delivery_costs.get(delivery_method, 0)
    grand_total = subtotal + delivery_cost

    if request.method == 'POST':
        # Создание заказа
        order = Order.objects.create(
            user=request.user,
            order_number=str(uuid.uuid4())[:8].upper(),
            total_amount=grand_total,
            delivery_method=delivery_method,
            delivery_cost=delivery_cost,
            notes=request.POST.get('notes', ''),
            status='pending'
        )

        # Добавление товаров в заказ
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.get_final_price()
            )

        # Очистка корзины
        cart.items.all().delete()

        messages.success(request, f'Заказ #{order.order_number} успешно оформлен!')
        return redirect('order_detail', order_id=order.id)

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'addresses': addresses,
        'subtotal': subtotal,
        'delivery_cost': delivery_cost,
        'grand_total': grand_total,
        'delivery_method': delivery_method,
    }
    return render(request, 'sportshop/checkout.html', context)


@customer_required
def order_detail(request, order_id):
    """Детальная страница заказа"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {
        'order': order,
        'order_items': order.items.all(),
    }
    return render(request, 'sportshop/order_detail.html', context)


# ==================== АУТЕНТИФИКАЦИЯ ====================
def login_view(request):
    """Страница входа"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль')

    return render(request, 'sportshop/login.html')


def register_view(request):
    """Страница регистрации"""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Создание профиля пользователя
            UserProfile.objects.create(user=user)

            # Добавление в группу покупателей
            from django.contrib.auth.models import Group
            try:
                customer_group = Group.objects.get(name='customer')
                user.groups.add(customer_group)
            except Group.DoesNotExist:
                pass

            # Автоматический вход после регистрации
            login(request, user)
            messages.success(request, f'Регистрация успешна! Добро пожаловать, {user.username}!')
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'sportshop/register.html', {'form': form})


def password_reset(request):
    """Упрощенная страница восстановления пароля"""
    if request.method == 'POST':
        email = request.POST.get('email')
        # Здесь должна быть логика отправки email
        messages.info(request, 'Если пользователь с таким email существует, вы получите инструкции по сбросу пароля.')
        return redirect('login')

    return render(request, 'sportshop/password_reset.html')


@login_required
def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('home')


# ==================== СТАТИЧЕСКИЕ СТРАНИЦЫ ====================
def about(request):
    """Страница "О нас" """
    return render(request, 'sportshop/about.html')


def contacts(request):
    """Страница контактов"""
    return render(request, 'sportshop/contacts.html')


def delivery_info(request):
    """Информация о доставке"""
    return render(request, 'sportshop/delivery.html')


def return_policy(request):
    """Условия возврата"""
    return render(request, 'sportshop/returns.html')


# ==================== API ДЛЯ УПРАВЛЕНИЯ ЗАКАЗАМИ ====================
@manager_required
def api_order_details(request, order_id):
    """API для получения деталей заказа (JSON)"""
    order = get_object_or_404(Order, id=order_id)

    # Собираем данные о товарах в заказе
    items = []
    for item in order.items.all():
        product_image = None
        if item.product and item.product.image:
            product_image = item.product.image.url

        items.append({
            'id': item.id,
            'product_id': item.product.id if item.product else None,
            'name': item.product.name if item.product else 'Товар удален',
            'quantity': item.quantity,
            'price': float(item.price),
            'total': float(item.quantity * item.price),
            'image': product_image,
        })

    # Данные пользователя
    user_data = {
        'id': order.user.id,
        'username': order.user.username,
        'email': order.user.email,
        'first_name': order.user.first_name,
        'last_name': order.user.last_name,
    }

    # Формируем полный ответ
    data = {
        'order_id': order.id,
        'order_number': order.order_number,
        'created_at': order.created_at.strftime('%d.%m.%Y %H:%M'),
        'status': order.status,
        'status_display': order.get_status_display(),
        'total_amount': float(order.total_amount),
        'subtotal': float(order.subtotal) if hasattr(order, 'subtotal') else float(order.total_amount),
        'delivery_cost': float(order.delivery_cost) if order.delivery_cost else 0,
        'delivery_method': order.delivery_method,
        'delivery_method_display': order.get_delivery_method_display() if hasattr(order,
                                                                                  'get_delivery_method_display') else order.delivery_method,
        'delivery_address': order.delivery_address if hasattr(order, 'delivery_address') else '',
        'delivery_city': order.delivery_city if hasattr(order, 'delivery_city') else '',
        'payment_method': order.payment_method,
        'payment_method_display': order.get_payment_method_display() if hasattr(order,
                                                                                'get_payment_method_display') else order.payment_method,
        'payment_status': order.payment_status,
        'payment_status_display': order.get_payment_status_display() if hasattr(order,
                                                                                'get_payment_status_display') else order.payment_status,
        'recipient_name': order.recipient_name if hasattr(order, 'recipient_name') else '',
        'recipient_phone': order.recipient_phone if hasattr(order, 'recipient_phone') else '',
        'notes': order.notes if hasattr(order, 'notes') else '',
        'user': user_data,
        'items': items,
    }

    return JsonResponse(data)


@manager_required
@require_POST
def api_update_order_status(request, order_id):
    """API для обновления статуса заказа (AJAX)"""
    try:
        data = json.loads(request.body)
        new_status = data.get('status')

        order = get_object_or_404(Order, id=order_id)
        old_status = order.status

        # Проверяем, что статус допустимый
        valid_statuses = dict(Order.STATUS_CHOICES).keys()
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': f'Недопустимый статус: {new_status}'
            }, status=400)

        # Обновляем статус
        order.status = new_status
        order.save()

        # Логируем изменение
        print(f"[{timezone.now()}] Статус заказа #{order.order_number} изменен: {old_status} -> {new_status}")

        return JsonResponse({
            'success': True,
            'message': 'Статус заказа обновлен',
            'order_id': order.id,
            'order_number': order.order_number,
            'new_status': new_status,
            'new_status_display': order.get_status_display(),
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат данных'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)