# setup_admin.py в корне проекта
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject2.settings')
django.setup()

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from sportshop.models import Product, Order, Category


def create_ordinary_admin():
    """Создает обычного администратора без прав суперпользователя"""

    # Создаем пользователя
    admin_user, created = User.objects.get_or_create(
        username='ordinary_admin',
        defaults={
            'email': 'admin@shop.ru',
            'is_staff': True,  # Может заходить в админку Django
            'is_superuser': False,  # НЕ суперпользователь!
        }
    )

    if created:
        admin_user.set_password('admin_password123')
        admin_user.save()
        print(f"Создан обычный администратор: {admin_user.username}")
    else:
        print(f"Администратор уже существует: {admin_user.username}")

    # Добавляем в группу администраторов
    admin_group, _ = Group.objects.get_or_create(name='administrator')
    admin_user.groups.add(admin_group)

    # Даем все разрешения
    all_permissions = Permission.objects.all()
    admin_group.permissions.set(all_permissions)

    print("\nПроверка прав:")
    print(f"  Username: {admin_user.username}")
    print(f"  Email: {admin_user.email}")
    print(f"  Is staff: {admin_user.is_staff}")
    print(f"  Is superuser: {admin_user.is_superuser}")
    print(f"  Groups: {[g.name for g in admin_user.groups.all()]}")
    print(f"  Permissions count: {admin_user.user_permissions.count()}")
    print(f"  Group permissions: {admin_group.permissions.count()}")

    # Проверяем доступ к админке
    print(f"\nДоступ к разделам админки:")
    print(f"  Пользователи: {admin_user.has_perm('auth.view_user')}")
    print(f"  Товары: {admin_user.has_perm('sportshop.view_product')}")
    print(f"  Заказы: {admin_user.has_perm('sportshop.view_order')}")

    return admin_user


if __name__ == '__main__':
    print("Создание обычного администратора...")
    admin = create_ordinary_admin()
    print(f"\nЛогин: {admin.username}")
    print(f"Пароль: admin_password123")
    print(f"Суперпользователь: {admin.is_superuser}")