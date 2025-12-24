# check_connection.py
print("=== ПРОВЕРКА ПОДКЛЮЧЕНИЯ К MYSQL ===")
print("Данные подключения:")
print("  Хост: localhost")
print("  Порт: 3307")
print("  Пользователь: root")
print("  Пароль: ")
print("  База: sport_shop")
print()

import pymysql

try:
    # 1. Проверяем подключение к MySQL
    print("1. Подключение к MySQL серверу...")
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        port=3307,
        charset='utf8mb4'
    )
    print("   ✅ MySQL доступен")

    cursor = conn.cursor()

    # 2. Проверяем версию
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()[0]
    print(f"   ✅ Версия MySQL: {version}")

    # 3. Проверяем/создаем базу sport_shop
    print("\n2. Проверка базы данных 'sport_shop'...")
    cursor.execute("SHOW DATABASES LIKE 'sport_shop'")

    if cursor.fetchone():
        print("   ✅ База 'sport_shop' существует")
    else:
        print("   ⚠️ База 'sport_shop' не найдена")
        print("   Создаю базу...")
        cursor.execute("CREATE DATABASE sport_shop CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("   ✅ База 'sport_shop' создана")

    conn.close()
    print("\n✅ Все проверки пройдены успешно!")

except pymysql.err.OperationalError as e:
    print(f"\n❌ ОШИБКА ПОДКЛЮЧЕНИЯ: {e}")
    print("\nВозможные решения:")
    print("1. Проверьте что MySQL запущен на порту 3307")
    print("2. Убедитесь что пароль '1234' правильный")
    print("3. Проверьте что пользователь 'root' существует")
    print("\nПроверка порта 3307:")
    import subprocess

    result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
    if '3307' in result.stdout:
        print("   ✅ Порт 3307 занят (MySQL вероятно запущен)")
    else:
        print("   ❌ Порт 3307 свободен (MySQL не запущен)")

except Exception as e:
    print(f"\n❌ НЕИЗВЕСТНАЯ ОШИБКА: {e}")