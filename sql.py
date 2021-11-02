import sqlite3

class SQLl:

    def __init__(self, database):
        """Подключаемся к БД и сохраняем курсор соединения"""
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def get_subscriptions(self, notifications = True):
        """Получаем всех активных подписчиков бота"""
        with self.connection:
            return self.cursor.execute("SELECT * FROM `subscriptions` WHERE `notifications` = ?", (notifications,)).fetchall()

    def subscriber_exists(self, user_id):
        """Проверяем, есть ли уже юзер в базе"""
        with self.connection:
            result = self.cursor.execute('SELECT * FROM `subscriptions` WHERE `user_id` = ?', (user_id,)).fetchall()
            return bool(len(result))

    def add_subscriber(self, user_id,notifications_currency, notifications = True):
        """Добавляем нового подписчика"""
        with self.connection:
            return self.cursor.execute("INSERT INTO `subscriptions` (`user_id`, `notifications`,'notifications_currency') VALUES(?,?,?)", (user_id,notifications,notifications_currency))

    def update_subscription(self, user_id, notifications_currency,notifications):
        """Обновляем статус подписки пользователя"""
        with self.connection:
            return self.cursor.execute("UPDATE `subscriptions` SET `notifications` = ?,'notifications_currency' = ? WHERE `user_id` = ?", (notifications,notifications_currency,user_id))

    def add_schdule(self, user_id,schedlue_currency, schedule_time,schedule = True):
        """Добавляем нового подписчика"""
        with self.connection:
            return self.cursor.execute("INSERT INTO `subscriptions` (`user_id`, `schedule`,'schedlue_currency','schedlue_currency' = ?) VALUES(?,?,?,?)", (user_id,schedule,schedlue_currency,schedule_time))

    def update_schedule(self, user_id, schedlue_currency,schedule_time,schedule):
        """Обновляем статус подписки пользователя"""
        with self.connection:
            return self.cursor.execute("UPDATE `subscriptions` SET `schedule` = ?,'schedlue_currency' = ?, 'schedule_time' = ? WHERE `user_id` = ?", (schedule,schedlue_currency,schedule_time,user_id))



    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()