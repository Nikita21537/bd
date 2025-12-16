# shop/context_processors.py
from .models import Category, CartItem


def cart_context(request):
    """Добавляет количество товаров в корзине в контекст"""
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(user=request.user).count()

    return {
        'cart_count': cart_count,
        'categories': Category.objects.all(),
    }