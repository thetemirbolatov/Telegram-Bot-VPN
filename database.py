import sqlite3
import json
import logging
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DB_PATH = 'vpn_bot.db'

# Инициализация базы данных
def init_database():
    """Создает все таблицы в базе данных"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица подписок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                server TEXT NOT NULL,
                config_file TEXT NOT NULL,
                purchase_date TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                duration TEXT,
                payment_id TEXT,
                promo_code TEXT,
                type TEXT DEFAULT 'paid',
                last_warnings TEXT DEFAULT '[]',
                expiry_notification_sent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, config_file)
            )
        ''')
        
        # Индексы для подписок
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_expiry_date ON subscriptions(expiry_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_config_file ON subscriptions(config_file)')
        
        # Таблица платежей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                username TEXT,
                server TEXT,
                duration TEXT,
                amount TEXT,
                bank TEXT,
                status TEXT DEFAULT 'pending',
                yookassa_payment_id TEXT,
                is_extension INTEGER DEFAULT 0,
                timestamp TEXT NOT NULL,
                approved_at TEXT,
                approved_by TEXT,
                rejected_at TEXT,
                rejected_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Индексы для платежей
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_payments_timestamp ON payments(timestamp)')
        
        # Таблица серверов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS servers (
                server_key TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT,
                load TEXT,
                protocol TEXT,
                ip TEXT,
                available_configs TEXT DEFAULT '[]',
                used_configs TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица промокодов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                server TEXT NOT NULL,
                days INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                created_by TEXT,
                created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица методов оплаты
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_methods (
                method_key TEXT PRIMARY KEY,
                bank TEXT NOT NULL,
                card_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица использованных промокодов пользователями
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_promo_codes (
                user_id TEXT NOT NULL,
                promo_code TEXT NOT NULL,
                used_at TEXT NOT NULL,
                PRIMARY KEY (user_id, promo_code),
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (promo_code) REFERENCES promo_codes(code)
            )
        ''')
        
        # Таблица для хранения временных данных пользователей (для состояний)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_states (
                user_id TEXT PRIMARY KEY,
                state_data TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Таблица для логов действий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        logger.info("База данных успешно инициализирована")

@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка БД: {e}")
        raise
    finally:
        conn.close()

# ============ ФУНКЦИИ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ============

def save_user_data(user_id, data):
    """Сохраняет или обновляет данные пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        username = data.get('username', '')
        
        # Проверяем существование пользователя
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (str(user_id),))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute('''
                UPDATE users 
                SET username = ?, data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (username, json.dumps(data, ensure_ascii=False), str(user_id)))
        else:
            cursor.execute('''
                INSERT INTO users (user_id, username, data)
                VALUES (?, ?, ?)
            ''', (str(user_id), username, json.dumps(data, ensure_ascii=False)))
        
        # Сохраняем подписки отдельно
        if 'subscriptions' in data:
            for sub in data['subscriptions']:
                cursor.execute('''
                    INSERT OR REPLACE INTO subscriptions 
                    (user_id, server, config_file, purchase_date, expiry_date, 
                     duration, payment_id, promo_code, type, last_warnings, expiry_notification_sent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(user_id),
                    sub.get('server', ''),
                    sub.get('config_file', ''),
                    sub.get('purchase_date', ''),
                    sub.get('expiry_date', ''),
                    sub.get('duration', ''),
                    sub.get('payment_id', ''),
                    sub.get('promo_code', ''),
                    sub.get('type', 'paid'),
                    json.dumps(sub.get('last_warnings', [])),
                    1 if sub.get('expiry_notification_sent', False) else 0
                ))
        
        # Сохраняем использованные промокоды
        if 'used_promo_codes' in data:
            for promo_code in data['used_promo_codes']:
                cursor.execute('''
                    INSERT OR IGNORE INTO user_promo_codes (user_id, promo_code, used_at)
                    VALUES (?, ?, ?)
                ''', (str(user_id), promo_code, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

def get_user_data(user_id):
    """Получает данные пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Получаем основную информацию
        cursor.execute('SELECT data FROM users WHERE user_id = ?', (str(user_id),))
        row = cursor.fetchone()
        
        if not row:
            return {}
        
        user_data = json.loads(row['data'])
        
        # Получаем подписки
        cursor.execute('''
            SELECT server, config_file, purchase_date, expiry_date, duration, 
                   payment_id, promo_code, type, last_warnings, expiry_notification_sent
            FROM subscriptions 
            WHERE user_id = ?
        ''', (str(user_id),))
        
        subscriptions = []
        for sub_row in cursor.fetchall():
            sub = {
                'server': sub_row['server'],
                'config_file': sub_row['config_file'],
                'purchase_date': sub_row['purchase_date'],
                'expiry_date': sub_row['expiry_date'],
                'duration': sub_row['duration'],
                'payment_id': sub_row['payment_id'],
                'promo_code': sub_row['promo_code'],
                'type': sub_row['type'],
                'last_warnings': json.loads(sub_row['last_warnings']) if sub_row['last_warnings'] else [],
                'expiry_notification_sent': bool(sub_row['expiry_notification_sent'])
            }
            subscriptions.append(sub)
        
        if subscriptions:
            user_data['subscriptions'] = subscriptions
        
        # Получаем использованные промокоды
        cursor.execute('SELECT promo_code FROM user_promo_codes WHERE user_id = ?', (str(user_id),))
        used_promo_codes = [row2['promo_code'] for row2 in cursor.fetchall()]
        if used_promo_codes:
            user_data['used_promo_codes'] = used_promo_codes
        
        return user_data

def get_all_users():
    """Возвращает всех пользователей"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, data FROM users')
        users = {}
        for row in cursor.fetchall():
            user_data = json.loads(row['data'])
            user_data['username'] = row['username']
            users[row['user_id']] = user_data
        return users

def user_exists(user_id):
    """Проверяет существование пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (str(user_id),))
        return cursor.fetchone() is not None

def delete_user(user_id):
    """Полностью удаляет пользователя и все его данные"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Удаляем подписки
        cursor.execute('DELETE FROM subscriptions WHERE user_id = ?', (str(user_id),))
        
        # Удаляем использованные промокоды
        cursor.execute('DELETE FROM user_promo_codes WHERE user_id = ?', (str(user_id),))
        
        # Удаляем состояния
        cursor.execute('DELETE FROM user_states WHERE user_id = ?', (str(user_id),))
        
        # Удаляем пользователя
        cursor.execute('DELETE FROM users WHERE user_id = ?', (str(user_id),))

# ============ ФУНКЦИИ ДЛЯ ПЛАТЕЖЕЙ ============

def save_payment(payment_id, data):
    """Сохраняет или обновляет платеж"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO payments 
            (payment_id, user_id, username, server, duration, amount, bank, status, 
             yookassa_payment_id, is_extension, timestamp, approved_at, approved_by, rejected_at, rejected_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            payment_id,
            str(data.get('user_id', '')),
            data.get('username', ''),
            data.get('server', ''),
            data.get('duration', ''),
            data.get('amount', ''),
            data.get('bank', ''),
            data.get('status', 'pending'),
            data.get('yookassa_payment_id', ''),
            1 if data.get('is_extension', False) else 0,
            data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            data.get('approved_at'),
            data.get('approved_by'),
            data.get('rejected_at'),
            data.get('rejected_by')
        ))

def get_payment(payment_id):
    """Получает данные платежа"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM payments WHERE payment_id = ?', (payment_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return {
            'user_id': row['user_id'],
            'username': row['username'],
            'server': row['server'],
            'duration': row['duration'],
            'amount': row['amount'],
            'bank': row['bank'],
            'status': row['status'],
            'yookassa_payment_id': row['yookassa_payment_id'],
            'is_extension': bool(row['is_extension']),
            'timestamp': row['timestamp'],
            'approved_at': row['approved_at'],
            'approved_by': row['approved_by'],
            'rejected_at': row['rejected_at'],
            'rejected_by': row['rejected_by']
        }

def get_all_payments():
    """Возвращает все платежи"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM payments')
        payments = {}
        for row in cursor.fetchall():
            payments[row['payment_id']] = {
                'user_id': row['user_id'],
                'username': row['username'],
                'server': row['server'],
                'duration': row['duration'],
                'amount': row['amount'],
                'bank': row['bank'],
                'status': row['status'],
                'yookassa_payment_id': row['yookassa_payment_id'],
                'is_extension': bool(row['is_extension']),
                'timestamp': row['timestamp'],
                'approved_at': row['approved_at'],
                'approved_by': row['approved_by']
            }
        return payments

def get_user_payments(user_id):
    """Возвращает платежи пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM payments WHERE user_id = ?', (str(user_id),))
        payments = {}
        for row in cursor.fetchall():
            payments[row['payment_id']] = {
                'user_id': row['user_id'],
                'username': row['username'],
                'server': row['server'],
                'duration': row['duration'],
                'amount': row['amount'],
                'bank': row['bank'],
                'status': row['status'],
                'timestamp': row['timestamp']
            }
        return payments

def update_payment_status(payment_id, status, approved_by=None, approved_at=None):
    """Обновляет статус платежа"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if status == 'approved':
            cursor.execute('''
                UPDATE payments 
                SET status = ?, approved_by = ?, approved_at = ?, updated_at = CURRENT_TIMESTAMP
                WHERE payment_id = ?
            ''', (status, approved_by, approved_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"), payment_id))
        elif status == 'rejected':
            cursor.execute('''
                UPDATE payments 
                SET status = ?, rejected_by = ?, rejected_at = ?, updated_at = CURRENT_TIMESTAMP
                WHERE payment_id = ?
            ''', (status, approved_by, approved_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"), payment_id))
        else:
            cursor.execute('''
                UPDATE payments 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE payment_id = ?
            ''', (status, payment_id))

# ============ ФУНКЦИИ ДЛЯ СЕРВЕРОВ ============

def save_server(server_key, server_data):
    """Сохраняет или обновляет данные сервера"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO servers 
            (server_key, name, location, load, protocol, ip, available_configs, used_configs)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            server_key,
            server_data.get('name', ''),
            server_data.get('location', ''),
            server_data.get('load', ''),
            server_data.get('protocol', ''),
            server_data.get('ip', ''),
            json.dumps(server_data.get('available_configs', [])),
            json.dumps(server_data.get('used_configs', {}))
        ))

def get_all_servers():
    """Возвращает все серверы"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM servers')
        servers = {}
        for row in cursor.fetchall():
            servers[row['server_key']] = {
                'name': row['name'],
                'location': row['location'],
                'load': row['load'],
                'protocol': row['protocol'],
                'ip': row['ip'],
                'available_configs': json.loads(row['available_configs']),
                'used_configs': json.loads(row['used_configs'])
            }
        return servers

def get_server(server_key):
    """Возвращает данные конкретного сервера"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM servers WHERE server_key = ?', (server_key,))
        row = cursor.fetchone()
        if row:
            return {
                'name': row['name'],
                'location': row['location'],
                'load': row['load'],
                'protocol': row['protocol'],
                'ip': row['ip'],
                'available_configs': json.loads(row['available_configs']),
                'used_configs': json.loads(row['used_configs'])
            }
        return None

def update_server_configs(server_key, available_configs, used_configs):
    """Обновляет конфиги сервера"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE servers 
            SET available_configs = ?, used_configs = ?, updated_at = CURRENT_TIMESTAMP
            WHERE server_key = ?
        ''', (json.dumps(available_configs), json.dumps(used_configs), server_key))

# ============ ФУНКЦИИ ДЛЯ ПРОМОКОДОВ ============

def save_promo_code(code, data):
    """Сохраняет промокод"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO promo_codes (code, server, days, created_at, created_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (code, data.get('server', ''), data.get('days', 0), data.get('created_at', ''), data.get('created_by', '')))

def get_all_promo_codes():
    """Возвращает все промокоды"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM promo_codes')
        promo_codes = {}
        for row in cursor.fetchall():
            promo_codes[row['code']] = {
                'server': row['server'],
                'days': row['days'],
                'created_at': row['created_at'],
                'created_by': row['created_by']
            }
        return promo_codes

def get_promo_code(code):
    """Возвращает данные промокода"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM promo_codes WHERE code = ?', (code,))
        row = cursor.fetchone()
        if row:
            return {
                'server': row['server'],
                'days': row['days'],
                'created_at': row['created_at'],
                'created_by': row['created_by']
            }
        return None

def delete_promo_code(code):
    """Удаляет промокод"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM promo_codes WHERE code = ?', (code,))

def is_promo_code_used_by_user(user_id, promo_code):
    """Проверяет, использовал ли пользователь промокод"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM user_promo_codes WHERE user_id = ? AND promo_code = ?', 
                      (str(user_id), promo_code))
        return cursor.fetchone() is not None

def add_user_promo_code(user_id, promo_code):
    """Добавляет использованный промокод пользователю"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO user_promo_codes (user_id, promo_code, used_at)
            VALUES (?, ?, ?)
        ''', (str(user_id), promo_code, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

# ============ ФУНКЦИИ ДЛЯ МЕТОДОВ ОПЛАТЫ ============

def save_payment_method(method_key, data):
    """Сохраняет метод оплаты"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO payment_methods (method_key, bank, card_number)
            VALUES (?, ?, ?)
        ''', (method_key, data.get('bank', ''), data.get('card_number', '')))

def get_all_payment_methods():
    """Возвращает все методы оплаты"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM payment_methods')
        methods = {}
        for row in cursor.fetchall():
            methods[row['method_key']] = {
                'bank': row['bank'],
                'card_number': row['card_number']
            }
        return methods

def delete_payment_method(method_key):
    """Удаляет метод оплаты"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM payment_methods WHERE method_key = ?', (method_key,))

# ============ ФУНКЦИИ ДЛЯ СОСТОЯНИЙ ПОЛЬЗОВАТЕЛЕЙ ============

def save_user_state(user_id, state_data):
    """Сохраняет временное состояние пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_states (user_id, state_data, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (str(user_id), json.dumps(state_data, ensure_ascii=False)))

def get_user_state(user_id):
    """Получает состояние пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT state_data FROM user_states WHERE user_id = ?', (str(user_id),))
        row = cursor.fetchone()
        if row:
            return json.loads(row['state_data'])
        return {}

def delete_user_state(user_id):
    """Удаляет состояние пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_states WHERE user_id = ?', (str(user_id),))

# ============ ФУНКЦИИ ДЛЯ ЛОГГИРОВАНИЯ ============

def log_action(user_id, action, details=None):
    """Логирует действие пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO action_logs (user_id, action, details)
            VALUES (?, ?, ?)
        ''', (str(user_id), action, json.dumps(details, ensure_ascii=False) if details else None))

def get_action_logs(limit=100, user_id=None):
    """Получает логи действий"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute('''
                SELECT * FROM action_logs 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (str(user_id), limit))
        else:
            cursor.execute('''
                SELECT * FROM action_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'action': row['action'],
                'details': json.loads(row['details']) if row['details'] else None,
                'timestamp': row['timestamp']
            })
        return logs

# ============ ФУНКЦИИ ДЛЯ МИГРАЦИИ ИЗ JSON ============

def migrate_from_json():
    """Мигрирует данные из JSON файлов в SQLite"""
    import os
    import json
    
    # Файлы для миграции
    json_files = {
        'users_db.json': 'users',
        'payments_db.json': 'payments',
        'servers_db.json': 'servers',
        'payment_methods.json': 'payment_methods',
        'promo_codes.json': 'promo_codes'
    }
    
    # Миграция пользователей
    if os.path.exists('users_db.json'):
        with open('users_db.json', 'r', encoding='utf-8') as f:
            users = json.load(f)
            for user_id, user_data in users.items():
                save_user_data(user_id, user_data)
        logger.info("Пользователи мигрированы")
    
    # Миграция платежей
    if os.path.exists('payments_db.json'):
        with open('payments_db.json', 'r', encoding='utf-8') as f:
            payments = json.load(f)
            for payment_id, payment_data in payments.items():
                save_payment(payment_id, payment_data)
        logger.info("Платежи мигрированы")
    
    # Миграция серверов
    if os.path.exists('servers_db.json'):
        with open('servers_db.json', 'r', encoding='utf-8') as f:
            servers = json.load(f)
            for server_key, server_data in servers.items():
                save_server(server_key, server_data)
        logger.info("Серверы мигрированы")
    
    # Миграция методов оплаты
    if os.path.exists('payment_methods.json'):
        with open('payment_methods.json', 'r', encoding='utf-8') as f:
            methods = json.load(f)
            for method_key, method_data in methods.items():
                save_payment_method(method_key, method_data)
        logger.info("Методы оплаты мигрированы")
    
    # Миграция промокодов
    if os.path.exists('promo_codes.json'):
        with open('promo_codes.json', 'r', encoding='utf-8') as f:
            promo_codes = json.load(f)
            for code, promo_data in promo_codes.items():
                save_promo_code(code, promo_data)
        logger.info("Промокоды мигрированы")
    
    logger.info("Миграция завершена!")
    
__all__ = [
    'init_database', 'get_db_connection', 'save_user_data', 'get_user_data', 
    'get_all_users', 'user_exists', 'delete_user', 'save_payment', 'get_payment',
    'get_all_payments', 'get_user_payments', 'update_payment_status',
    'get_all_servers', 'get_server', 'update_server_configs', 'save_server',
    'save_promo_code', 'get_all_promo_codes', 'get_promo_code', 'delete_promo_code',
    'is_promo_code_used_by_user', 'add_user_promo_code', 'save_payment_method',
    'get_all_payment_methods', 'delete_payment_method', 'save_user_state',
    'get_user_state', 'delete_user_state', 'log_action', 'get_action_logs',
    'migrate_from_json', 'DB_PATH'
]

# Инициализация БД при импорте
init_database()