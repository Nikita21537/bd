from .models import Cart


def cart_context(request):
    """
    Добавляет информацию о корзине в контекст всех шаблонов
    """
    context = {}

    if request.user.is_authenticated:
        from .models import Cart
        try:
            cart = Cart.objects.get(user=request.user)
            context['cart_count'] = cart.get_total_quantity()
            context['cart_total'] = cart.get_total_price()
        except Cart.DoesNotExist:
            context['cart_count'] = 0
            context['cart_total'] = 0
    else:
        context['cart_count'] = 0
        context['cart_total'] = 0

    return context
def cart_count(request):
    """Добавляет счетчик корзины в контекст всех шаблонов"""
    cart_count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_count = cart.get_total_quantity()
    return {'cart_count': cart_count}