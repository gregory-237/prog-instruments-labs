import sqlite3

from config import DB_NAME
from bot_logger import configured_logger


class DatabaseWorker:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS workers
                              (user_id INT PRIMARY KEY, phone_number TEXT, fio TEXT, city TEXT, status INT)''')
        self.conn.commit()

    def is_registered(self, user_id) -> bool:
        with self.conn:
            if self.cursor.execute('''SELECT * from workers WHERE user_id = ?''',
                                   (
                                           user_id,)).fetchall():
                return True
            else:
                return False

    def is_admin(self, user_id) -> bool:
        with self.conn:
            if self.cursor.execute('''SELECT status from workers WHERE user_id = ?''',
                                   (
                                           user_id,)).fetchone()[0] == 1:
                return True
            else:
                return False

    def info_worker(self, user_id) -> tuple:
        with self.conn:
            return self.cursor.execute('''SELECT * from workers WHERE user_id = ?''',
                                       (
                                           user_id,)).fetchone()

    def add_worker(self, user_id, phone_number, fio, city, status=0):
        self.cursor.execute('''INSERT INTO workers (user_id, phone_number,
         fio, city, status) VALUES (?, ?, ?, ?, ?)''', (user_id, phone_number, fio, city, status))
        self.conn.commit()
        configured_logger.info('Зарегистрирован новый рабочий', user_id=user_id, role='worker',
                               ext_params={
                                  'Номер телефона': phone_number,
                                  'ФИО': fio,
                                  'Город': city,
                              })

    def all_worker_id_by_city(self, city: str):
        with self.conn:
            return self.cursor.execute('''SELECT user_id from workers WHERE status = 0 AND city = ?''',
                                       (city,)).fetchall()

