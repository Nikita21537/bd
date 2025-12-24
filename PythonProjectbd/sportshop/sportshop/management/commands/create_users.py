# sportshop/management/commands/create_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from sportshop.models import Product, Order, Category


class Command(BaseCommand):
    help = 'Создает тестовых пользователей с разными ролями'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Удалить существующих тестовых пользователей перед созданием',
        )

    def handle(self, *args, **options):

        if options['reset']:
            # Удаляем тестовых пользователей
            test_users = User.objects.filter(
                username__in=['customer', 'manager', 'admin_ordinary', 'superadmin']
            )
            deleted_count, _ = test_users.delete()
            self.stdout.write(self.style.WARNING(f'Удалено {deleted_count} тестовых пользователей'))

        # Создаем группы если их нет
        groups = {
            'customer': 'Покупатель',
            'manager': 'Менеджер',
            'administrator': 'Администратор'
        }

        for name, verbose in groups.items():
            Group.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS(f'Группа "{name}" создана/найдена'))

        # Создаем или находим разрешения
        self.setup_permissions()

        # Пользователи
        users_data = [
            # Обычный покупатель
            {
                'username': 'customer',
                'email': 'customer@example.com',
                'password': 'customer123',
                'is_staff': False,
                'is_superuser': False,
                'groups': ['customer']
            },
            # Менеджер
            {
                'username': 'manager',
                'email': 'manager@example.com',
                'password': 'manager123',
                'is_staff': True,
                'is_superuser': False,
                'groups': ['manager']
            },
            # Обычный администратор (НЕ суперпользователь)
            {
                'username': 'admin_ordinary',
                'email': 'admin@example.com',
                'password': 'admin123',
                'is_staff': True,  # Может заходить в админку
                'is_superuser': False,  # НЕ суперпользователь!
                'groups': ['administrator']
            },
            # Суперпользователь для сравнения
            {
                'username': 'superadmin',
                'email': 'superadmin@example.com',
                'password': 'superadmin123',
                'is_staff': True,
                'is_superuser': True,
                'groups': []
            }
        ]

        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'is_staff': user_data['is_staff'],
                    'is_superuser': user_data['is_superuser']
                }
            )

            if created:
                user.set_password(user_data['password'])
                user.save()

                # Очищаем существующие группы
                user.groups.clear()

                # Назначаем группы
                for group_name in user_data['groups']:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)

                self.stdout.write(self.style.SUCCESS(
                    f'Создан пользователь: {user.username} '
                    f'(суперпользователь: {user.is_superuser}, персонал: {user.is_staff})'
                ))
            else:
                # Обновляем существующего пользователя
                user.email = user_data['email']
                user.is_staff = user_data['is_staff']
                user.is_superuser = user_data['is_superuser']
                user.set_password(user_data['password'])
                user.save()

                # Очищаем и обновляем группы
                user.groups.clear()
                for group_name in user_data['groups']:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)

                self.stdout.write(self.style.WARNING(
                    f'Обновлен пользователь: {user.username} '
                    f'(суперпользователь: {user.is_superuser}, персонал: {user.is_staff})'
                ))

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 50))
        self.stdout.write(self.style.SUCCESS('Тестовые пользователи созданы:'))
        self.stdout.write(self.style.SUCCESS('1. customer/customer123 - обычный покупатель'))
        self.stdout.write(self.style.SUCCESS('2. manager/manager123 - менеджер'))
        self.stdout.write(self.style.SUCCESS('3. admin_ordinary/admin123 - обычный администратор'))
        self.stdout.write(self.style.SUCCESS('4. superadmin/superadmin123 - суперпользователь'))
        self.stdout.write(self.style.SUCCESS('=' * 50))

    def setup_permissions(self):
        """Настраивает разрешения для групп"""

        # Получаем ContentType для моделей
        try:
            # Для моделей из вашего приложения
            from sportshop.models import Product, Order, Category, Review, UserProfile, Address
            from django.contrib.auth.models import User

            # Получаем ContentType для всех нужных моделей
            models_to_setup = [
                ('product', Product),
                ('order', Order),
                ('category', Category),
                ('review', Review),
                ('userprofile', UserProfile),
                ('address', Address),
                ('user', User),
            ]

            permissions_added = 0

            for app_label, model in models_to_setup:
                try:
                    ct = ContentType.objects.get(app_label='sportshop', model=app_label)

                    # Получаем все разрешения для этой модели
                    model_permissions = Permission.objects.filter(content_type=ct)

                    # Добавляем все разрешения в группу администраторов
                    admin_group = Group.objects.get(name='administrator')
                    for perm in model_permissions:
                        admin_group.permissions.add(perm)
                        permissions_added += 1

                except ContentType.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'ContentType не найден для {app_label}'))
                    continue

            self.stdout.write(self.style.SUCCESS(f'Добавлено {permissions_added} разрешений в группу администраторов'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при настройке разрешений: {e}'))