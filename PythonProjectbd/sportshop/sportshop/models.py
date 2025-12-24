from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class Category(models.Model):
    """Категории товаров"""
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField('URL', max_length=50, unique=True)  # ← ДОБАВЬТЕ max_length=50
    description = models.TextField('Описание', blank=True)
    image = models.CharField('Изображение', max_length=100, blank=True, null=True)  # ← ИЗМЕНИТЕ НА CharField
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        db_table = 'sportshop_category'  # ← ЯВНО укажите имя таблицы

    def __str__(self):
        return self.name

    def get_product_count(self):
        return self.products.count()


class Product(models.Model):
    """Товары"""
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField('URL', unique=True)
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        on_delete=models.CASCADE,
        related_name='products'
    )
    sku = models.CharField('Артикул', max_length=50, unique=True, blank=True)

    description = models.TextField('Описание')
    short_description = models.CharField('Краткое описание', max_length=255, blank=True)

    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        'Цена со скидкой',
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    image = models.ImageField('Основное изображение', upload_to='products/')
    images = models.ManyToManyField(
        'ProductImage',
        verbose_name='Дополнительные изображения',
        blank=True,
        related_name='product_set'
    )

    stock_quantity = models.PositiveIntegerField('Количество на складе', default=0)
    in_stock = models.BooleanField('В наличии', default=True)

    # Технические характеристики
    weight = models.DecimalField('Вес (кг)', max_digits=6, decimal_places=2, blank=True, null=True)
    dimensions = models.CharField('Размеры (ШxВxГ)', max_length=50, blank=True)
    material = models.CharField('Материал', max_length=100, blank=True)
    brand = models.CharField('Бренд', max_length=100, blank=True)

    # Метаданные
    views = models.PositiveIntegerField('Просмотры', default=0)
    rating = models.DecimalField('Рейтинг', max_digits=3, decimal_places=2, default=0)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    is_active = models.BooleanField('Активный', default=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['price']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.name

    def get_final_price(self):
        """Получить окончательную цену (со скидкой если есть)"""
        return self.discount_price if self.discount_price else self.price

    def get_discount_percentage(self):
        """Рассчитать процент скидки"""
        if self.discount_price and self.price > 0:
            discount = ((self.price - self.discount_price) / self.price) * 100
            return round(discount)
        return 0

    def get_saving_amount(self):
        """Сколько денег экономит покупатель"""
        if self.discount_price:
            return self.price - self.discount_price
        return 0

    def is_available(self):
        """Доступен ли товар для заказа"""
        return self.in_stock and self.stock_quantity > 0

    def get_average_rating(self):
        """Средний рейтинг товара"""
        reviews = self.reviews.all()
        if reviews:
            total = sum(review.rating for review in reviews)
            return round(total / len(reviews), 1)
        return 0

    def save(self, *args, **kwargs):
        # Автоматически генерируем артикул если не указан
        if not self.sku:
            self.sku = f"PROD-{uuid.uuid4().hex[:8].upper()}"

        # Обновляем поле in_stock в зависимости от количества
        self.in_stock = self.stock_quantity > 0

        super().save(*args, **kwargs)


class ProductImage(models.Model):
    """Дополнительные изображения товаров"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='additional_images'
    )
    image = models.ImageField('Изображение', upload_to='products/additional/')
    alt_text = models.CharField('Alt текст', max_length=100, blank=True)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
        ordering = ['order']

    def __str__(self):
        return f"Изображение для {self.product.name}"


class Review(models.Model):
    """Отзывы о товарах"""
    RATING_CHOICES = [
        (1, '1 - Очень плохо'),
        (2, '2 - Плохо'),
        (3, '3 - Удовлетворительно'),
        (4, '4 - Хорошо'),
        (5, '5 - Отлично'),
    ]

    product = models.ForeignKey(
        Product,
        verbose_name='Товар',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.IntegerField('Оценка', choices=RATING_CHOICES, default=5)
    comment = models.TextField('Комментарий')
    advantages = models.TextField('Достоинства', blank=True)
    disadvantages = models.TextField('Недостатки', blank=True)

    is_verified_purchase = models.BooleanField('Подтвержденная покупка', default=False)
    is_published = models.BooleanField('Опубликован', default=True)

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
        unique_together = ['product', 'user']

    def __str__(self):
        return f"Отзыв {self.user.username} на {self.product.name}"

    def get_rating_stars(self):
        """Получить HTML для отображения звезд рейтинга"""
        stars_full = '★' * self.rating
        stars_empty = '☆' * (5 - self.rating)
        return stars_full + stars_empty


class Cart(models.Model):
    """Корзина покупок"""
    user = models.OneToOneField(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    session_key = models.CharField('Ключ сессии', max_length=40, blank=True, null=True)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f"Корзина {self.user.username}"

    def get_total_quantity(self):
        """Общее количество товаров в корзине"""
        return sum(item.quantity for item in self.items.all())

    def get_total_price(self):
        """Общая стоимость товаров в корзине"""
        total = sum(item.get_total_price() for item in self.items.all())

        # Применяем скидку если есть
        if hasattr(self, 'coupon') and self.coupon:
            total = self.coupon.apply_discount(total)

        return total

    def clear(self):
        """Очистить корзину"""
        self.items.all().delete()
        if hasattr(self, 'coupon'):
            self.coupon.delete()


class CartItem(models.Model):
    """Товары в корзине"""
    cart = models.ForeignKey(
        Cart,
        verbose_name='Корзина',
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        verbose_name='Товар',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField('Количество', default=1)
    added_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        """Общая стоимость позиции"""
        return self.product.get_final_price() * self.quantity


class Order(models.Model):
    """Заказы"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
        ('refunded', 'Возвращен'),
    ]

    DELIVERY_CHOICES = [
        ('pickup', 'Самовывоз'),
        ('courier', 'Курьерская доставка'),
        ('post', 'Почта России'),
        ('cdek', 'СДЭК'),
    ]

    PAYMENT_CHOICES = [
        ('card', 'Картой онлайн'),
        ('cash', 'Наличными при получении'),
        ('invoice', 'Безналичный расчет'),
    ]

    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    order_number = models.CharField('Номер заказа', max_length=20, unique=True)

    # Информация о доставке
    delivery_method = models.CharField(
        'Способ доставки',
        max_length=20,
        choices=DELIVERY_CHOICES,
        default='courier'
    )
    delivery_cost = models.DecimalField(
        'Стоимость доставки',
        max_digits=8,
        decimal_places=2,
        default=0
    )

    # Адрес доставки
    recipient_name = models.CharField('Имя получателя', max_length=100)
    recipient_phone = models.CharField('Телефон получателя', max_length=20)
    delivery_address = models.TextField('Адрес доставки')
    delivery_city = models.CharField('Город', max_length=100)
    delivery_postal_code = models.CharField('Индекс', max_length=10, blank=True)

    # Платежная информация
    payment_method = models.CharField(
        'Способ оплаты',
        max_length=20,
        choices=PAYMENT_CHOICES,
        default='card'
    )
    payment_status = models.CharField(
        'Статус оплаты',
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Ожидает оплаты'),
            ('paid', 'Оплачен'),
            ('failed', 'Ошибка оплаты'),
            ('refunded', 'Возвращен'),
        ]
    )

    # Статус заказа
    status = models.CharField(
        'Статус заказа',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Стоимость
    subtotal = models.DecimalField('Стоимость товаров', max_digits=10, decimal_places=2)
    discount = models.DecimalField('Скидка', max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField('Итоговая сумма', max_digits=10, decimal_places=2)

    # Дополнительная информация
    notes = models.TextField('Комментарий к заказу', blank=True)
    tracking_number = models.CharField('Трек номер', max_length=50, blank=True)

    # Даты
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    paid_at = models.DateTimeField('Дата оплаты', blank=True, null=True)
    delivered_at = models.DateTimeField('Дата доставки', blank=True, null=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Заказ #{self.order_number}"

    def generate_order_number(self):
        """Генерация номера заказа"""
        if not self.order_number:
            date_str = timezone.now().strftime('%Y%m%d')
            self.order_number = f"ORD-{date_str}-{uuid.uuid4().hex[:6].upper()}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.generate_order_number()
        super().save(*args, **kwargs)

    def get_status_display_class(self):
        """CSS класс для отображения статуса"""
        status_classes = {
            'pending': 'status-pending',
            'processing': 'status-processing',
            'shipped': 'status-shipped',
            'delivered': 'status-delivered',
            'cancelled': 'status-cancelled',
            'refunded': 'status-cancelled',
        }
        return status_classes.get(self.status, '')

    def get_items_count(self):
        """Количество товаров в заказе"""
        return self.items.count()

    def can_be_cancelled(self):
        """Можно ли отменить заказ"""
        return self.status in ['pending', 'processing']


class OrderItem(models.Model):
    """Товары в заказе"""
    order = models.ForeignKey(
        Order,
        verbose_name='Заказ',
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        verbose_name='Товар',
        on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField('Количество', default=1)
    price = models.DecimalField('Цена за единицу', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        """Общая стоимость позиции"""
        return self.price * self.quantity


class UserProfile(models.Model):
    """Расширенный профиль пользователя"""
    user = models.OneToOneField(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # Контактная информация
    phone = models.CharField('Телефон', max_length=20, blank=True)
    birth_date = models.DateField('Дата рождения', blank=True, null=True)

    # Статистика
    bonus_points = models.PositiveIntegerField('Бонусные баллы', default=0)
    total_orders = models.PositiveIntegerField('Всего заказов', default=0)
    total_spent = models.DecimalField(
        'Всего потрачено',
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # Настройки
    receive_newsletter = models.BooleanField('Получать рассылку', default=True)
    email_notifications = models.BooleanField('Email уведомления', default=True)

    # Аватары
    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
        blank=True,
        null=True,
        default='avatars/default.png'
    )

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f"Профиль {self.user.username}"

    def get_full_name(self):
        """Полное имя пользователя"""
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username

    def add_bonus_points(self, points):
        """Добавить бонусные баллы"""
        self.bonus_points += points
        self.save()

    def spend_bonus_points(self, points):
        """Потратить бонусные баллы"""
        if self.bonus_points >= points:
            self.bonus_points -= points
            self.save()
            return True
        return False


class Address(models.Model):
    """Адреса доставки пользователей"""
    ADDRESS_TYPES = [
        ('home', 'Дом'),
        ('work', 'Работа'),
        ('other', 'Другой'),
    ]

    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    address_type = models.CharField(
        'Тип адреса',
        max_length=10,
        choices=ADDRESS_TYPES,
        default='home'
    )

    # Основная информация
    name = models.CharField('Название', max_length=100, help_text="Например: Дом, Работа")
    recipient_name = models.CharField('Имя получателя', max_length=100)
    phone = models.CharField('Телефон', max_length=20)

    # Адрес
    country = models.CharField('Страна', max_length=50, default='Россия')
    city = models.CharField('Город', max_length=100)
    street = models.TextField('Улица, дом, квартира')
    postal_code = models.CharField('Почтовый индекс', max_length=10, blank=True)

    # Дополнительно
    is_default = models.BooleanField('Основной адрес', default=False)
    notes = models.TextField('Примечания', blank=True)

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Адрес'
        verbose_name_plural = 'Адреса'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.name} - {self.city}, {self.street[:30]}..."

    def get_full_address(self):
        """Полный адрес в формате строки"""
        parts = [
            f"г. {self.city}",
            self.street,
        ]
        if self.postal_code:
            parts.insert(1, f"индекс {self.postal_code}")

        return ", ".join(parts)

    def save(self, *args, **kwargs):
        # Если адрес помечен как основной, снимаем этот флаг с других адресов пользователя
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)

        super().save(*args, **kwargs)