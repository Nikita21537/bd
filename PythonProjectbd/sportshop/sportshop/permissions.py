"""
Система прав доступа для SportShop
Роли:
1. customer (покупатель) - обычный пользователь
2. manager (менеджер) - управление товарами и заказами
3. administrator (администратор) - полные права
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Order, Category, User


def setup_user_groups():
    """
    Настройка групп пользователей при первом запуске
    Вызывается из post_migrate сигнала
    """
    print("Настройка групп пользователей...")

    # Создаем группы, если их нет
    customer_group, created = Group.objects.get_or_create(name='customer')
    if created:
        print(f"Создана группа: {customer_group.name}")

    manager_group, created = Group.objects.get_or_create(name='manager')
    if created:
        print(f"Создана группа: {manager_group.name}")

    admin_group, created = Group.objects.get_or_create(name='administrator')
    if created:
        print(f"Создана группа: {admin_group.name}")

    # Получаем разрешения для разных моделей
    try:
        content_type_product = ContentType.objects.get_for_model(Product)
        content_type_order = ContentType.objects.get_for_model(Order)
        content_type_category = ContentType.objects.get_for_model(Category)
        content_type_user = ContentType.objects.get_for_model(User)

        # Разрешения для товаров
        product_perms = Permission.objects.filter(content_type=content_type_product)
        # Разрешения для заказов
        order_perms = Permission.objects.filter(content_type=content_type_order)
        # Разрешения для категорий
        category_perms = Permission.objects.filter(content_type=content_type_category)
        # Разрешения для пользователей
        user_perms = Permission.objects.filter(content_type=content_type_user)

        # Настраиваем права для покупателя (только просмотр)
        customer_group.permissions.clear()

        # Покупатель может просматривать товары, категории и свои заказы
        view_product = Permission.objects.get(codename='view_product', content_type=content_type_product)
        view_category = Permission.objects.get(codename='view_category', content_type=content_type_category)

        customer_group.permissions.add(view_product, view_category)
        print(f"Настроены права для группы: {customer_group.name}")

        # Настраиваем права для менеджера
        manager_group.permissions.clear()

        # Менеджер может всё с товарами, заказами, категориями
        manager_perms = list(product_perms) + list(order_perms) + list(category_perms)
        # Исключаем права на удаление пользователей
        manager_perms = [p for p in manager_perms if 'user' not in p.codename]

        manager_group.permissions.set(manager_perms)
        print(f"Настроены права для группы: {manager_group.name}")

        # Настраиваем права для администратора (все права)
        admin_group.permissions.clear()
        all_perms = Permission.objects.all()
        admin_group.permissions.set(all_perms)
        print(f"Настроены права для группы: {admin_group.name}")

        print("Группы пользователей успешно настроены!")

    except Exception as e:
        print(f"Ошибка при настройке групп: {e}")

    return {
        'customer': customer_group,
        'manager': manager_group,
        'admin': admin_group
    }


# Декораторы для проверки прав
def customer_required(view_func):
    """
    Требует, чтобы пользователь был покупателем или выше
    Проверка через группы пользователей
    """

    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        user = request.user

        # Суперпользователь имеет все права
        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Проверяем группы пользователя
        user_groups = user.groups.values_list('name', flat=True)

        # Если пользователь в любой из групп - разрешаем доступ
        if any(group in user_groups for group in ['customer', 'manager', 'administrator']):
            return view_func(request, *args, **kwargs)

        # Если пользователь без группы - добавляем в покупатели
        if not user_groups:
            try:
                customer_group = Group.objects.get(name='customer')
                user.groups.add(customer_group)
                return view_func(request, *args, **kwargs)
            except Group.DoesNotExist:
                # Если группы нет - создаем её
                setup_user_groups()
                customer_group = Group.objects.get(name='customer')
                user.groups.add(customer_group)
                return view_func(request, *args, **kwargs)

        raise PermissionDenied("Требуется авторизация как покупатель")

    return _wrapped_view


def manager_required(view_func):
    """
    Требует, чтобы пользователь был менеджером или администратором
    """

    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        user = request.user

        # Суперпользователь имеет все права
        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Проверяем группы пользователя
        user_groups = user.groups.values_list('name', flat=True)

        # Разрешаем доступ менеджерам и администраторам
        if any(group in user_groups for group in ['manager', 'administrator']):
            return view_func(request, *args, **kwargs)

        raise PermissionDenied("Требуются права менеджера или администратора")

    return _wrapped_view


def admin_required(view_func):
    """
    Требует, чтобы пользователь был администратором
    """

    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        user = request.user

        # Суперпользователь имеет все права
        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Проверяем группы пользователя
        user_groups = user.groups.values_list('name', flat=True)

        # Разрешаем доступ только администраторам
        if 'administrator' in user_groups:
            return view_func(request, *args, **kwargs)

        raise PermissionDenied("Требуются права администратора")

    return _wrapped_view


# Функции проверки прав на уровне объекта
def check_object_permission(user, obj, action):
    """
    Проверка прав на конкретный объект
    action: 'view', 'change', 'delete'
    """
    if user.is_superuser:
        return True

    user_groups = user.groups.values_list('name', flat=True)

    if action == 'view':
        # Все авторизованные могут просматривать свои объекты
        if hasattr(obj, 'user') and obj.user == user:
            return True

        # Менеджеры и администраторы могут просматривать все
        if any(group in user_groups for group in ['manager', 'administrator']):
            return True

        # Покупатели могут просматривать только публичные объекты
        if hasattr(obj, 'is_active'):
            return obj.is_active
        if hasattr(obj, 'is_published'):
            return obj.is_published

    elif action == 'change':
        # Пользователь может изменять только свои объекты
        if hasattr(obj, 'user') and obj.user == user:
            return True

        # Менеджеры и администраторы могут изменять все
        if any(group in user_groups for group in ['manager', 'administrator']):
            return True

    elif action == 'delete':
        # Обычные пользователи не могут удалять
        # Только менеджеры и администраторы
        if any(group in user_groups for group in ['manager', 'administrator']):
            return True

    return False


def get_user_role(user):
    """
    Получить роль пользователя
    Возвращает: 'customer', 'manager', 'admin', или 'superuser'
    """
    if user.is_superuser:
        return 'superuser'

    user_groups = user.groups.values_list('name', flat=True)

    if 'administrator' in user_groups:
        return 'admin'
    elif 'manager' in user_groups:
        return 'manager'
    elif 'customer' in user_groups:
        return 'customer'
    else:
        # Если нет группы - считаем покупателем
        try:
            customer_group = Group.objects.get(name='customer')
            user.groups.add(customer_group)
            return 'customer'
        except:
            return 'customer'


def has_permission(user, permission_codename):
    """
    Проверяет, есть ли у пользователя конкретное разрешение
    """
    if user.is_superuser:
        return True

    # Проверяем через группы
    return user.groups.filter(permissions__codename=permission_codename).exists() or \
        user.user_permissions.filter(codename=permission_codename).exists()


# Сигнал для автоматической настройки групп после миграций
def setup_groups_on_startup():
    """
    Функция для вызова при старте приложения
    """
    try:
        # Проверяем, есть ли уже группы
        if not Group.objects.exists():
            setup_user_groups()
        else:
            # Проверяем, есть ли все нужные группы
            required_groups = ['customer', 'manager', 'administrator']
            existing_groups = Group.objects.values_list('name', flat=True)

            missing_groups = [g for g in required_groups if g not in existing_groups]
            if missing_groups:
                setup_user_groups()
    except:
        # Игнорируем ошибки при первом запуске (ещё нет таблиц)
        pass