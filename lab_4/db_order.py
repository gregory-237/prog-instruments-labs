import sqlite3

from config import DB_NAME
from bot_logger import configured_logger


class DatabaseOrder:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS orders
                              (order_id TEXT PRIMARY KEY, worker_id INT DEFAULT 0, worker_group INT DEFAULT 0, city TEXT, group_number TEXT, minimum TEXT, address TEXT, time_start TEXT, time_work TEXT, price_hour TEXT, status INT, desc TEXT)''')
        self.conn.commit()

    def add_order(self, admin_id: int, order_id: str, city: str, group_number: str, minimum: str, address: str,
                  time_start: str, time_work: str, price_hour: str, desc: str, status: int = 0):
        self.cursor.execute(
            '''INSERT INTO orders (order_id, city, group_number, minimum, address, time_start, time_work, price_hour, status, desc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (order_id, city,
             group_number, minimum, address, time_start, time_work, price_hour, status, desc,))
        self.conn.commit()
        configured_logger.info('Добавлена заявка на работы', user_id=admin_id, role='admin', ext_params={
            'Город': city, 'Количество людей': group_number, 'Адрес': address, 'Время начала': time_start,
            'Время работы': time_work, 'Оплата в час': price_hour,
        })

    def all_orders(self, user_id) -> list:
        with self.conn:
            return self.cursor.execute('''SELECT * from orders WHERE worker_id = ?''',
                                       (
                                           user_id,)).fetchall()

    def select_info_order(self, order_id) -> tuple:
        with self.conn:
            return self.cursor.execute('''SELECT * from orders WHERE order_id = ?''',
                                       (
                                           order_id,)).fetchone()

    def update_after_confirm(self, admin_id: int, order_id, worker_id, worker_group):
        self.cursor.execute(
            f'''UPDATE orders SET worker_id = {worker_id} WHERE order_id = ?''', (
                (order_id,)
            ))
        self.cursor.execute('''UPDATE orders SET status = 1 WHERE order_id = ?''', (
            (order_id,)
        ))
        self.cursor.execute(f'''UPDATE orders SET worker_group = {worker_group} WHERE order_id = ?''', (
            (order_id,)
        ))
        self.conn.commit()
        configured_logger.info('Изменены данные заявки после подтверждения админом', user_id=admin_id, role='admin', ext_params={
            'ID рабочего': admin_id, 'Количество людей': worker_group,
        })




