import requests
from getpass import getpass

BASE_URL = 'http://localhost:5000/api'

# 1. Получить все товары
response = requests.get(f'{BASE_URL}/products')
print("Все товары:", response.json())

# 2. Получить один товар
response = requests.get(f'{BASE_URL}/products/1')
print("Товар 1:", response.json())

# 3. Создать товар (нужны админские права)
email = input("Введите email админа: ")
password = getpass("Введите пароль: ")

new_product = {
    "title": "Горный воздух",
    "price": 500.0,
    "quantity": 50,
    "category": "air",
    "description": "Свежий воздух с гор"
}

response = requests.post(
    f'{BASE_URL}/products',
    json=new_product,
    auth=(email, password)
)
print("Создание товара:", response.json())

# 4. Получить заказы
response = requests.get(
    f'{BASE_URL}/orders',
    auth=(email, password)
)
print("Ваши заказы:", response.json())