import pymysql
import os
from pathlib import Path

# ========== ДОБАВЬТЕ В САМОЕ НАЧАЛО ФАЙЛА ==========
# Исправляем версию PyMySQL для совместимости с Django
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.__version__ = "2.2.1"

# Устанавливаем PyMySQL как драйвер MySQL для Django
pymysql.install_as_MySQLdb()
# ===================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-change-this-in-production-12345'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'sportshop',

    # ← Основное приложение
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'DjangoProject2.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'sportshop/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'sportshop.context_processors.cart_context',  # ← Добавьте этот контекстный процессор
            ],
        },
    },
]

WSGI_APPLICATION = 'DjangoProject2.wsgi.application'

# ========== ВАШИ НАСТРОЙКИ БАЗЫ ДАННЫХ ==========
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sport_shop',      # Имя базы данных
        'USER': 'root',            # Пользователь
        'PASSWORD': '',            # Пароль
        'HOST': 'localhost',       # Хост
        'PORT': '3307',            # Порт
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

# ========== НАСТРОЙКИ ДЛЯ ЗАГРУЗКИ ФАЙЛОВ ==========
# Медиа файлы (загружаемые пользователями)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Статические файлы
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'sportshop/static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ========== НАСТРОЙКИ АУТЕНТИФИКАЦИИ ==========
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'login'           # куда перенаправлять если доступ запрещён
LOGIN_REDIRECT_URL = '/'      # куда идти после успешного входа
LOGOUT_REDIRECT_URL = '/'     # куда идти после выхода

# ========== ЛОКАЛИЗАЦИЯ ==========
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# ========== ДРУГИЕ НАСТРОЙКИ ==========
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
INTERNAL_IPS = ['127.0.0.1']

# ========== АВТОМАТИЧЕСКАЯ НАСТРОЙКА ГРУПП ==========
# Автоматическое создание групп пользователей при запуске
import sys
if 'migrate' not in sys.argv and 'makemigrations' not in sys.argv:
    try:
        from sportshop.permissions import setup_groups_on_startup
        setup_groups_on_startup()
    except:
        pass 