# sportshop/management/commands/seed_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from decimal import Decimal
import random
from sportshop.models import (
    Category, Product, ProductImage, UserProfile,
    Address, Order, OrderItem, Review, Cart, CartItem
)


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными'

    def handle(self, *args, **kwargs):
        self.stdout.write('Начинаю заполнение базы данных...')

        # Создание групп пользователей
        self.create_user_groups()

        # Создание пользователей
        admin_user = self.create_admin_user()
        customer_users = self.create_customer_users()

        # Создание категорий
        categories = self.create_categories()

        # Создание товаров
        products = self.create_products(categories)

        # Создание профилей пользователей
        self.create_user_profiles(admin_user, customer_users)

        # Создание адресов
        addresses = self.create_addresses(customer_users)

        # Создание заказов
        orders = self.create_orders(customer_users, products, addresses)

        # Создание отзывов
        self.create_reviews(customer_users, products, orders)

        # Создание корзин
        self.create_carts(customer_users, products)

        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена!'))

    def create_user_groups(self):
        """Создание групп пользователей"""
        groups = ['customer', 'manager', 'administrator']
        for group_name in groups:
            Group.objects.get_or_create(name=group_name)
        self.stdout.write('Группы пользователей созданы')

    def create_admin_user(self):
        """Создание администратора"""
        admin, created = User.objects.get_or_create(
            username='admin_ordinary',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            admin_group = Group.objects.get(name='administrator')
            admin.groups.add(admin_group)
            self.stdout.write('Администратор создан')
        return admin

    def create_customer_users(self):
        """Создание покупателей"""
        customers_data = [
            {'username': 'ivan', 'first_name': 'Иван', 'last_name': 'Петров', 'email': 'ivan@example.com'},
            {'username': 'maria', 'first_name': 'Мария', 'last_name': 'Сидорова', 'email': 'maria@example.com'},
            {'username': 'alex', 'first_name': 'Алексей', 'last_name': 'Иванов', 'email': 'alex@example.com'},
            {'username': 'olga', 'first_name': 'Ольга', 'last_name': 'Смирнова', 'email': 'olga@example.com'},
            {'username': 'dmitry', 'first_name': 'Дмитрий', 'last_name': 'Кузнецов', 'email': 'dmitry@example.com'},
        ]

        customer_group = Group.objects.get(name='customer')
        customers = []

        for data in customers_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                }
            )
            if created:
                user.set_password('customer123')
                user.save()
                user.groups.add(customer_group)
                customers.append(user)

        self.stdout.write(f'Создано {len(customers)} покупателей')
        return customers

    def create_categories(self):
        """Создание категорий"""
        categories_data = [
            {'name': 'Футбол', 'slug': 'football', 'description': 'Всё для игры в футбол'},
            {'name': 'Баскетбол', 'slug': 'basketball', 'description': 'Оборудование для баскетбола'},
            {'name': 'Теннис', 'slug': 'tennis', 'description': 'Теннисные ракетки и мячи'},
            {'name': 'Бег', 'slug': 'running', 'description': 'Одежда и обувь для бега'},
            {'name': 'Йога', 'slug': 'yoga', 'description': 'Коврики и аксессуары для йоги'},
            {'name': 'Тренажеры', 'slug': 'fitness', 'description': 'Домашние тренажеры'},
            {'name': 'Велоспорт', 'slug': 'cycling', 'description': 'Велосипеды и аксессуары'},
            {'name': 'Плавание', 'slug': 'swimming', 'description': 'Спортивное плавание'},
        ]

        categories = []
        for data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=data['slug'],
                defaults=data
            )
            if created:
                categories.append(category)

        self.stdout.write(f'Создано {len(categories)} категорий')
        return categories

    def create_products(self, categories):
        """Создание товаров"""
        products_data = [
            {
                'name': 'Футбольный мяч Adidas',
                'slug': 'football-ball-adidas',
                'category': categories[0],
                'price': Decimal('2999.99'),
                'discount_price': Decimal('2499.99'),
                'description': 'Профессиональный футбольный мяч',
                'stock_quantity': 50,
                'brand': 'Adidas',
                'material': 'Полиуретан'
            },
            {
                'name': 'Баскетбольный мяч Spalding',
                'slug': 'basketball-ball-spalding',
                'category': categories[1],
                'price': Decimal('4599.99'),
                'description': 'Официальный мяч для соревнований',
                'stock_quantity': 30,
                'brand': 'Spalding',
                'material': 'Кожа'
            },
            {
                'name': 'Теннисная ракетка Wilson',
                'slug': 'tennis-racket-wilson',
                'category': categories[2],
                'price': Decimal('8999.99'),
                'discount_price': Decimal('7499.99'),
                'description': 'Легкая ракетка для профессионалов',
                'stock_quantity': 20,
                'brand': 'Wilson',
                'material': 'Графит'
            },
            {
                'name': 'Футбольные бутсы Nike',
                'slug': 'football-boots-nike',
                'category': categories[0],
                'price': Decimal('7999.99'),
                'discount_price': Decimal('6999.99'),
                'description': 'Бутсы с шипами для игры на траве',
                'stock_quantity': 25,
                'brand': 'Nike',
                'material': 'Кожа'
            },
            {
                'name': 'Кроссовки для бега Asics',
                'slug': 'running-shoes-asics',
                'category': categories[3],
                'price': Decimal('5999.99'),
                'description': 'Удобные кроссовки для бега',
                'stock_quantity': 40,
                'brand': 'Asics'
            },
            {
                'name': 'Коврик для йоги',
                'slug': 'yoga-mat',
                'category': categories[4],
                'price': Decimal('1999.99'),
                'description': 'Антискользящий коврик',
                'stock_quantity': 100,
                'brand': 'SportElite'
            },
            {
                'name': 'Гантели 5 кг',
                'slug': 'dumbbells-5kg',
                'category': categories[5],
                'price': Decimal('1499.99'),
                'description': 'Набор гантелей',
                'stock_quantity': 60,
                'brand': 'Torneo'
            },
            {
                'name': 'Велосипед горный',
                'slug': 'mountain-bike',
                'category': categories[6],
                'price': Decimal('25999.99'),
                'description': 'Горный велосипед 21 скорость',
                'stock_quantity': 10,
                'brand': 'Forward'
            },
            {
                'name': 'Очки для плавания',
                'slug': 'swimming-goggles',
                'category': categories[7],
                'price': Decimal('999.99'),
                'description': 'Профессиональные очки',
                'stock_quantity': 80,
                'brand': 'Arena'
            },
        ]

        products = []
        for i, data in enumerate(products_data):
            sku = f"PROD-{1000 + i}"
            product, created = Product.objects.get_or_create(
                slug=data['slug'],
                defaults={
                    **data,
                    'sku': sku,
                    'short_description': data['description'][:100],
                    'in_stock': data['stock_quantity'] > 0,
                    'views': random.randint(50, 300),
                    'rating': Decimal(random.uniform(3.5, 5.0)).quantize(Decimal('0.1')),
                    'created_at': timezone.now() - timezone.timedelta(days=random.randint(1, 30)),
                    'is_active': True
                }
            )
            if created:
                products.append(product)

        self.stdout.write(f'Создано {len(products)} товаров')
        return products

    def create_user_profiles(self, admin_user, customer_users):
        """Создание профилей пользователей"""
        # Профиль администратора
        UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                'phone': '+79160000001',
                'bonus_points': 5000,
                'total_orders': 0,
                'total_spent': Decimal('0'),
            }
        )

        # Профили покупателей
        for i, user in enumerate(customer_users):
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'phone': f'+791600000{10 + i}',
                    'bonus_points': random.randint(100, 1000),
                    'total_orders': random.randint(1, 10),
                    'total_spent': Decimal(random.randint(5000, 50000)),
                    'birth_date': f'199{random.randint(0, 9)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}',
                }
            )

        self.stdout.write('Профили пользователей созданы')

    def create_addresses(self, customer_users):
        """Создание адресов"""
        addresses = []
        cities = ['Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань']

        for user in customer_users:
            for i in range(random.randint(1, 3)):
                address = Address.objects.create(
                    user=user,
                    name=f'Адрес {i + 1}',
                    address_type=random.choice(['home', 'work', 'other']),
                    recipient_name=f'{user.first_name} {user.last_name}',
                    phone=user.profile.phone,
                    city=random.choice(cities),
                    street=f'ул. {random.choice(["Ленина", "Пушкина", "Мира", "Советская"])}, д. {random.randint(1, 100)}, кв. {random.randint(1, 100)}',
                    postal_code=f'{random.randint(100000, 199999)}',
                    is_default=(i == 0)
                )
                addresses.append(address)

        self.stdout.write(f'Создано {len(addresses)} адресов')
        return addresses

    def create_orders(self, customer_users, products, addresses):
        """Создание заказов"""
        orders = []
        statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        payment_methods = ['card', 'cash', 'invoice']
        delivery_methods = ['pickup', 'courier', 'post', 'cdek']

        for i in range(20):  # Создаем 20 тестовых заказов
            user = random.choice(customer_users)
            user_addresses = [a for a in addresses if a.user == user]
            address = random.choice(user_addresses) if user_addresses else None

            order = Order.objects.create(
                user=user,
                order_number=f"ORD-{timezone.now().strftime('%Y%m%d')}-{1000 + i}",
                delivery_method=random.choice(delivery_methods),
                delivery_cost=Decimal(random.choice([0, 250, 300, 350])),
                recipient_name=address.recipient_name if address else f'{user.first_name} {user.last_name}',
                recipient_phone=address.phone if address else user.profile.phone,
                delivery_address=address.street if address else 'Адрес не указан',
                delivery_city=address.city if address else 'Москва',
                delivery_postal_code=address.postal_code if address else '101000',
                payment_method=random.choice(payment_methods),
                payment_status=random.choice(['pending', 'paid', 'failed']),
                status=random.choice(statuses),
                subtotal=Decimal('0'),
                total_amount=Decimal('0'),
                notes=random.choice(['', 'Позвонить перед доставкой', 'Оставить у двери', '']),
                created_at=timezone.now() - timezone.timedelta(days=random.randint(1, 60))
            )

            # Добавляем товары в заказ
            order_items = random.sample(products, random.randint(1, 3))
            subtotal = Decimal('0')

            for product in order_items:
                quantity = random.randint(1, 3)
                price = product.get_final_price()
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price
                )
                subtotal += price * quantity

            # Обновляем суммы заказа
            order.subtotal = subtotal
            order.total_amount = subtotal + order.delivery_cost
            order.save()

            # Обновляем даты в зависимости от статуса
            if order.status in ['shipped', 'delivered']:
                order.paid_at = order.created_at + timezone.timedelta(hours=1)
                if order.status == 'delivered':
                    order.delivered_at = order.created_at + timezone.timedelta(days=random.randint(1, 5))
            order.save()

            orders.append(order)

        self.stdout.write(f'Создано {len(orders)} заказов')
        return orders

    def create_reviews(self, customer_users, products, orders):
        """Создание отзывов"""
        reviews_count = 0

        for order in orders:
            # Для некоторых заказов создаем отзывы
            if random.random() > 0.5:  # 50% вероятность отзыва
                for item in order.items.all():
                    if random.random() > 0.7:  # 30% вероятность отзыва на товар
                        Review.objects.create(
                            product=item.product,
                            user=order.user,
                            rating=random.randint(3, 5),
                            comment=random.choice([
                                'Отличный товар!',
                                'Хорошее качество',
                                'Доволен покупкой',
                                'Могло быть и лучше',
                                'Соответствует описанию'
                            ]),
                            advantages=random.choice([
                                'Качество, цена',
                                'Долговечность',
                                'Удобство использования'
                            ]),
                            disadvantages=random.choice([
                                'Нет недостатков',
                                'Цена немного высокая',
                                '',
                                'Долгая доставка'
                            ]),
                            is_verified_purchase=True,
                            is_published=True,
                            created_at=order.created_at + timezone.timedelta(days=random.randint(1, 7))
                        )
                        reviews_count += 1

        self.stdout.write(f'Создано {reviews_count} отзывов')

    def create_carts(self, customer_users, products):
        """Создание корзин"""
        for user in customer_users:
            cart, created = Cart.objects.get_or_create(user=user)
            if created:
                # Добавляем случайные товары в корзину
                cart_products = random.sample(products, random.randint(0, 3))
                for product in cart_products:
                    CartItem.objects.create(
                        cart=cart,
                        product=product,
                        quantity=random.randint(1, 2)
                    )

        self.stdout.write('Корзины созданы')