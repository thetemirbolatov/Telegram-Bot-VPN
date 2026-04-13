import uuid
import logging
from yookassa import Configuration, Payment
from datetime import datetime

logger = logging.getLogger(__name__)

# Настройки ЮKassa
YOOKASSA_SHOP_ID = "введи свой id"
YOOKASSA_SECRET_KEY = "введи свой ключ"

# Инициализация ЮKassa
Configuration.configure(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)

def create_yookassa_payment(amount, description, payment_id, user_id, username, payment_method=None):
    """Создает платеж в ЮKassa с выбором способа оплаты"""
    try:
        # Формируем уникальный ID платежа
        idempotence_key = str(uuid.uuid4())
        
        # Базовые параметры платежа
        payment_params = {
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/karachay_aj_bot?check_payment_{payment_id}"
            },
            "description": description,
            "metadata": {
                "payment_id": payment_id,
                "user_id": str(user_id),
                "username": username,
                "amount": amount
            },
            "capture": True
        }
        
        # Добавляем метод оплаты если указан (для тестового магазина доступны карты и ЮMoney)
        if payment_method:
            payment_methods_map = {
                "bank_card": {"type": "bank_card"},
                "yoo_money": {"type": "yoo_money"},
                "sberbank": {"type": "sberbank"},
                "alfabank": {"type": "alfabank"},
                "tinkoff_bank": {"type": "tinkoff_bank"},
                "mobile_balance": {"type": "mobile_balance"}
            }
            
            if payment_method in payment_methods_map:
                payment_params["payment_method_data"] = payment_methods_map[payment_method]
        
        # Создаем платеж
        payment = Payment.create(payment_params, idempotence_key)
        
        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "status": payment.status
        }
    except Exception as e:
        logger.error(f"Ошибка создания платежа ЮKassa: {e}")
        return None

def create_payment_with_methods_menu(user_id, amount, description, payment_id, username):
    """Создает платеж с выбором способа оплаты через меню"""
    try:
        # Создаем платеж с возможностью выбора способа
        idempotence_key = str(uuid.uuid4())
        
        payment_params = {
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/karachay_aj_bot?check_payment_{payment_id}"
            },
            "description": description,
            "metadata": {
                "payment_id": payment_id,
                "user_id": str(user_id),
                "username": username,
                "amount": amount
            },
            "capture": True
        }
        
        payment = Payment.create(payment_params, idempotence_key)
        
        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "status": payment.status
        }
    except Exception as e:
        logger.error(f"Ошибка создания платежа: {e}")
        return None

def check_payment_status(payment_id):
    """Проверяет статус платежа в ЮKassa"""
    try:
        payment = Payment.find_one(payment_id)
        return {
            "status": payment.status,
            "paid": payment.paid,
            "amount": payment.amount.value if hasattr(payment, 'amount') else None
        }
    except Exception as e:
        logger.error(f"Ошибка проверки платежа: {e}")
        return None

def capture_payment(payment_id):
    """Подтверждает платеж (если нужно)"""
    try:
        payment = Payment.capture(payment_id)
        return payment.status == "succeeded"
    except Exception as e:
        logger.error(f"Ошибка подтверждения платежа: {e}")
        return False