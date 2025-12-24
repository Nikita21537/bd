import os
import django
from datetime import date

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject2.settings')
django.setup()

from django.contrib.auth.models import User
from sportshop.models import UserProfile


def create_test_users():
    """Создание тестовых пользователей с понятными паролями"""

    # Список пользователей для создания
    test_users = [
        {
            'username': 'customer1',
            'password': 'customer123',
            'email': 'customer1@example.com',
            'first_name': 'Александр',
            'last_name': 'Иванов',
            'phone': '+79161112233',
            'birth_date': date(1990, 5, 15),
            'bonus_points': 150,
        },
        {
            'username': 'customer2',
            'password': 'customer123',
            'email': 'customer2@example.com',
            'first_name': 'Екатерина',
            'last_name': 'Смирнова',
            'phone': '+79162223344',
            'birth_date': date(1985, 8, 22),
            'bonus_points': 250,
        },
        {
            'username': 'sportsman',
            'password': 'sport12345',
            'email': 'sportsman@example.com',
            'first_name': 'Дмитрий',
            'last_name': 'Петров',
            'phone': '+79163334455',
            'birth_date': date(1992, 3, 10),
            'bonus_points': 500,
        },
        {
            'username': 'fitgirl',
            'password': 'fit12345',
            'email': 'fitgirl@example.com',
            'first_name': 'Анна',
            'last_name': 'Кузнецова',
            'phone': '+79164445566',
            'birth_date': date(1995, 11, 30),
            'bonus_points': 300,
        },
        {
            'username': 'coach',
            'password': 'coach1234',
            'email': 'coach@example.com',
            'first_name': 'Сергей',
            'last_name': 'Васильев',
            'phone': '+79165556677',
            'birth_date': date(1980, 7, 5),
            'bonus_points': 1000,
        },
        {
            'username': 'yoga_lover',
            'password': 'yoga12345',
            'email': 'yoga@example.com',
            'first_name': 'Ольга',
            'last_name': 'Николаева',
            'phone': '+79166667788',
            'birth_date': date(1988, 12, 18),
            'bonus_points': 180,
        },
        {
            'username': 'runner',
            'password': 'run123456',
            'email': 'runner@example.com',
            'first_name': 'Михаил',
            'last_name': 'Федоров',
            'phone': '+79167778899',
            'birth_date': date(1993, 4, 25),
            'bonus_points': 400,
        },
        {
            'username': 'teamplayer',
            'password': 'team12345',
            'email': 'team@example.com',
            'first_name': 'Артем',
            'last_name': 'Соколов',
            'phone': '+79168889900',
            'birth_date': date(1991, 9, 14),
            'bonus_points': 220,
        },
        {
            'username': 'gym_rat',
            'password': 'gym123456',
            'email': 'gym@example.com',
            'first_name': 'Владимир',
            'last_name': 'Попов',
            'phone': '+79169990011',
            'birth_date': date(1987, 2, 28),
            'bonus_points': 750,
        },
        {
            'username': 'tennis_pro',
            'password': 'tennis123',
            'email': 'tennis@example.com',
            'first_name': 'Татьяна',
            'last_name': 'Лебедева',
            'phone': '+79161010101',
            'birth_date': date(1983, 6, 8),
            'bonus_points': 600,
        },
    ]

    created_users = []
    existing_users = []

    print("=" * 60)
    print("СОЗДАНИЕ ТЕСТОВЫХ ПОЛЬЗОВАТЕЛЕЙ")
    print("=" * 60)

    for user_data in test_users:
        # Проверяем, существует ли пользователь
        if User.objects.filter(username=user_data['username']).exists():
            existing_users.append(user_data['username'])
            print(f"❌ Пользователь '{user_data['username']}' уже существует")
            continue

        # Создаем пользователя
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )

        # Создаем профиль пользователя
        UserProfile.objects.create(
            user=user,
            phone=user_data['phone'],
            birth_date=user_data['birth_date'],
            bonus_points=user_data['bonus_points']
        )

        created_users.append({
            'username': user_data['username'],
            'password': user_data['password'],
            'name': f"{user_data['first_name']} {user_data['last_name']}"
        })

        print(
            f"✅ Создан: {user_data['username']} / {user_data['password']} - {user_data['first_name']} {user_data['last_name']}")

    print("=" * 60)
    print("ИТОГИ:")
    print(f"✅ Создано новых пользователей: {len(created_users)}")
    print(f"⚠️ Уже существовало: {len(existing_users)}")
    print("=" * 60)

    # Сохраняем логины и пароли в файл
    if created_users:
        with open('user_credentials.txt', 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("ТЕСТОВЫЕ ПОЛЬЗОВАТЕЛИ - ЛОГИНЫ И ПАРОЛИ\n")
            f.write("=" * 60 + "\n\n")
            for i, user in enumerate(created_users, 1):
                f.write(f"{i}. {user['name']}\n")
                f.write(f"   Логин: {user['username']}\n")
                f.write(f"   Пароль: {user['password']}\n")
                f.write("-" * 40 + "\n")

        print("📄 Логины и пароли сохранены в файл 'user_credentials.txt'")

    return created_users


def create_admin_user():
    """Создание дополнительного администратора"""
    if not User.objects.filter(username='admin2').exists():
        admin_user = User.objects.create_superuser(
            username='admin2',
            email='admin2@example.com',
            password='admin12345',
            first_name='Администратор',
            last_name='Второй'
        )
        print(f"👑 Создан администратор: admin2 / admin12345")
        return admin_user
    else:
        print("⚠️ Администратор admin2 уже существует")
        return None


def show_all_users():
    """Показать всех пользователей"""
    print("\n" + "=" * 60)
    print("ВСЕ ПОЛЬЗОВАТЕЛИ В СИСТЕМЕ")
    print("=" * 60)

    users = User.objects.all().order_by('date_joined')
    for i, user in enumerate(users, 1):
        user_type = "👑 АДМИН" if user.is_superuser else "👤 ПОЛЬЗОВАТЕЛЬ"
        profile = getattr(user, 'profile', None)
        bonus = profile.bonus_points if profile else 0

        print(f"{i}. {user_type}: {user.username}")
        print(f"   Имя: {user.get_full_name() or 'Не указано'}")
        print(f"   Email: {user.email}")
        print(f"   Бонусы: {bonus}")
        print(f"   Дата регистрации: {user.date_joined.strftime('%d.%m.%Y')}")
        print("-" * 40)


def main():
    print("\n🚀 ЗАПУСК СКРИПТА СОЗДАНИЯ ПОЛЬЗОВАТЕЛЕЙ")
    print("=" * 60)

    # Создаем тестовых пользователей
    created_users = create_test_users()

    # Создаем дополнительного администратора (опционально)
    create_admin = input("\nСоздать дополнительного администратора? (y/n): ").lower()
    if create_admin == 'y':
        create_admin_user()

    # Показать всех пользователей
    show_all = input("\nПоказать всех пользователей в системе? (y/n): ").lower()
    if show_all == 'y':
        show_all_users()

    print("\n" + "=" * 60)
    print("✅ СКРИПТ УСПЕШНО ВЫПОЛНЕН")
    print("=" * 60)

    if created_users:
        print("\nДля входа используйте:")
        print("1. customer1 / customer123")
        print("2. sportsman / sport12345")
        print("3. fitgirl / fit12345")
        print("\nВсе логины и пароли сохранены в файле 'user_credentials.txt'")


if __name__ == "__main__":
    main()