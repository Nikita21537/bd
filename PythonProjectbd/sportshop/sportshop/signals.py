from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Product, Order, Category, User, Review
from .permissions import setup_user_groups


@receiver(post_migrate)
def setup_default_groups(sender, **kwargs):
    """
    Автоматически создает группы и настраивает права после миграций
    """
    if sender.name == 'sportshop':
        setup_user_groups()