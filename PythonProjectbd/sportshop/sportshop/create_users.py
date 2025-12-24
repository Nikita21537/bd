from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group


class Command(BaseCommand):
    help = 'Создает тестовых пользователей с разными ролями'

    def handle(self, *args, **kwargs):
        # Создаем группы если их нет
        groups = {
            'customer': 'Покупатель',
            'manager': 'Менеджер',
            'administrator': 'Администратор'
        }

        for name, verbose in groups.items():
            Group.objects.get_or_create(name=name)
            self.stdout.write(self.style.SUCCESS(f'Группа "{name}" создана'))

        # Пользователи
        users = [
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

        for user_data in users:
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

                # Назначаем группы
                for group_name in user_data['groups']:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)

                self.stdout.write(self.style.SUCCESS(
                    f'Создан пользователь: {user.username} '
                    f'(суперпользователь: {user.is_superuser}, персонал: {user.is_staff})'
                ))

        self.stdout.write(self.style.SUCCESS('\nТестовые пользователи созданы:'))
        self.stdout.write('1. customer/customer123 - обычный покупатель')
        self.stdout.write('2. manager/manager123 - менеджер (доступ к товарам и заказам)')
        self.stdout.write('3. admin_ordinary/admin123 - обычный администратор (все права, кроме суперпользователя)')
        self.stdout.write('4. superadmin/superadmin123 - суперпользователь (все права)')