# sportshop/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    Category, Product, ProductImage, Review,
    Cart, CartItem, Order, OrderItem,
    UserProfile, Address
)
from django.contrib import messages
from django.http import HttpResponseRedirect


# Регистрация UserProfile как inline в User
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'groups', 'date_joined']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Обычные администраторы видят всех пользователей
        if request.user.is_superuser or request.user.groups.filter(name='administrator').exists():
            return qs
        # Менеджеры не видят пользователей
        return qs.none()

    def has_module_permission(self, request):
        # Только суперадмины и администраторы видят раздел пользователей
        return request.user.is_superuser or request.user.groups.filter(name='administrator').exists()


# Отменяем стандартную регистрацию User и регистрируем с inline
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

    def has_delete_permission(self, request, obj=None):
        # Только администраторы могут удалять категории
        if request.user.is_superuser or request.user.groups.filter(name='administrator').exists():
            return True
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'discount_price', 'in_stock', 'created_at']
    list_filter = ['category', 'in_stock', 'is_active']
    search_fields = ['name', 'description', 'sku']
    list_editable = ['price', 'discount_price', 'in_stock']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['images']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'category', 'sku', 'description')
        }),
        ('Цены и наличие', {
            'fields': ('price', 'discount_price', 'stock_quantity', 'in_stock')
        }),
        ('Изображения', {
            'fields': ('image', 'images')
        }),
        ('Характеристики', {
            'fields': ('weight', 'dimensions', 'material', 'brand')
        }),
        ('Метаданные', {
            'fields': ('rating', 'views', 'is_active')
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # Только администраторы могут удалять товары
        if request.user.is_superuser or request.user.groups.filter(name='administrator').exists():
            return True
        return False

    def get_readonly_fields(self, request, obj=None):
        # Менеджеры могут редактировать, но не удалять
        readonly_fields = []
        if request.user.groups.filter(name='manager').exists():
            # Менеджеры не могут менять некоторые поля
            readonly_fields = ['rating', 'views']
        return readonly_fields


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'alt_text', 'order']
    list_filter = ['product']
    ordering = ['product', 'order']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_published', 'created_at']
    list_filter = ['rating', 'is_published', 'is_verified_purchase']
    search_fields = ['product__name', 'user__username', 'comment']
    list_editable = ['is_published']

    def has_delete_permission(self, request, obj=None):
        # Только администраторы могут удалять отзывы
        if request.user.is_superuser or request.user.groups.filter(name='administrator').exists():
            return True
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'payment_status', 'delivery_method', 'created_at']
    search_fields = ['order_number', 'user__username', 'recipient_name']
    list_editable = ['status']
    readonly_fields = ['order_number', 'created_at', 'updated_at']

    def has_delete_permission(self, request, obj=None):
        # Только администраторы могут удалять заказы
        if request.user.is_superuser or request.user.groups.filter(name='administrator').exists():
            return True
        return False


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    list_filter = ['order__status']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_total_quantity', 'get_total_price', 'updated_at']

    def get_total_quantity(self, obj):
        return obj.get_total_quantity()
    get_total_quantity.short_description = 'Кол-во товаров'

    def get_total_price(self, obj):
        return obj.get_total_price()
    get_total_price.short_description = 'Общая сумма'

    def has_module_permission(self, request):
        # Только суперадмины и администраторы видят корзины
        return request.user.is_superuser or request.user.groups.filter(name='administrator').exists()


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'added_at']

    def has_module_permission(self, request):
        # Только суперадмины и администраторы видят элементы корзины
        return request.user.is_superuser or request.user.groups.filter(name='administrator').exists()


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'bonus_points', 'total_orders', 'total_spent']
    search_fields = ['user__username', 'phone']
    list_filter = ['receive_newsletter']

    def has_module_permission(self, request):
        # Только суперадмины и администраторы видят профили
        return request.user.is_superuser or request.user.groups.filter(name='administrator').exists()


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'city', 'is_default', 'address_type']
    list_filter = ['address_type', 'is_default', 'city']
    search_fields = ['user__username', 'city', 'street']

    def has_module_permission(self, request):
        # Только суперадмины и администраторы видят адреса
        return request.user.is_superuser or request.user.groups.filter(name='administrator').exists()