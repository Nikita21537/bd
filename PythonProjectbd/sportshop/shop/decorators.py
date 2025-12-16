# shop/decorators.py
from django.core.exceptions import PermissionDenied
from functools import wraps

def manager_required(view_func):
    """Требует роль Менеджер или Администратор"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.has_manager_permissions():
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_required(view_func):
    """Требует роль Администратор"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.has_admin_permissions():
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper