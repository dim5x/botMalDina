import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Класс для управления базой данных SQLite."""

    def __init__(self, db_name: str = "support_bot.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        """Создает и возвращает соединение с базой данных."""
        return sqlite3.connect(self.db_name)

    def init_db(self) -> None:
        """Инициализирует таблицы в базе данных."""
        create_faq_table = """
        CREATE TABLE IF NOT EXISTS faq_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            keywords TEXT NOT NULL
        )
        """

        create_feedbacks_table = """
        CREATE TABLE IF NOT EXISTS feedbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    message TEXT NOT NULL,
    media_type TEXT,
    media_file_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(create_faq_table)
                cursor.execute(create_feedbacks_table)
                conn.commit()
                logger.info("Database tables initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")

    def add_faq_item(self, question: str, answer: str, keywords: str) -> None:
        """Добавляет новый вопрос-ответ в базу FAQ."""
        insert_query = """
        INSERT INTO faq_items (question, answer, keywords)
        VALUES (?, ?, ?)
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_query, (question, answer, keywords))
                conn.commit()
                logger.info(f"FAQ item added: {question}")
        except sqlite3.Error as e:
            logger.error(f"Error adding FAQ item: {e}")

    import json
    import sqlite3
    from typing import List, Tuple

    def search_faq(self, user_message: str) -> List[Tuple[str, str]]:
        """
        Ищет подходящие ответы в FAQ по ключевым словам.
        Возвращает список подходящих записей (вопрос, ответ).
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Получаем все записи из FAQ
                cursor.execute("SELECT question, answer, keywords FROM faq_items")
                all_faq_items = cursor.fetchall()

                # Приводим сообщение пользователя к нижнему регистру
                user_message_lower = user_message.lower()

                results = []
                for question, answer, keywords in all_faq_items:
                    # Проверяем, есть ли хотя бы одно ключевое слово в сообщении пользователя
                    for keyword in keywords.split():
                        if keyword.lower() in user_message_lower:
                            results.append((question, answer))
                            break  # Добавляем запись только один раз

                return results

        except sqlite3.Error as e:
            logger.error(f"Error searching FAQ: {e}")
            return []

    # Обновляем метод add_feedback
    # В методе add_feedback добавляем параметры для медиа
    def add_feedback(self, user_id: int, username: str, message: str,
                     media_type: str = None, media_file_id: str = None) -> None:
        """Добавляет отзыв или обратную связь в базу данных."""
        insert_query = """
        INSERT INTO feedbacks (user_id, username, message, media_type, media_file_id)
        VALUES (?, ?, ?, ?, ?)
        """

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_query, (user_id, username, message, media_type, media_file_id))
                conn.commit()
                logger.info(f"Feedback added from user {user_id}")
        except sqlite3.Error as e:
            logger.error(f"Error adding feedback: {e}")


# Создаем глобальный экземпляр менеджера БД
db_manager = DatabaseManager()


def populate_initial_data() -> None:
    """Заполняет базу данных первоначальными данными FAQ."""
    initial_data = [
        {
            "question": "Как оставить отзыв и получить бонус?",
            "answer": "После публикации отзыва сделайте скриншот, пришлите его в ответ на это сообщение и укажите удобный способ получения бонуса (только для покупателей из РФ).",
            "keywords": "отзыв бонус скриншот получить"
        },
        {
            "question": "Как подтвердить брак товара?",
            "answer": "Для подтверждения брака подробно опишите проблему:\n1. В чем заключается неисправность\n2. Когда получили заказ\n3. Был ли товар в использовании\n4. Прикрепите фото и/или видео, на которых видно неисправность",
            "keywords": "брак неисправность дефект поломка повреждение"
        },
        {
            "question": "Где можно оставить обратную связь?",
            "answer": "Здесь можно оставить отзыв о работе нашего магазина, чата поддержки или товара, а также рассказать о пожеланиях.",
            "keywords": "обратная связь отзыв пожелания предложения"
        },
        {
            "question": "Какие категории товаров есть в магазине?",
            "answer": "В нашем магазине представлены следующие категории: Панты, Массажеры, Игрушечное оружие и другие товары.",
            "keywords": "категории товары ассортимент панты массажеры оружие"
        }
    ]

    for item in initial_data:
        db_manager.add_faq_item(
            item["question"],
            item["answer"],
            item["keywords"]
        )


# Заполняем базу初始ными данными при импорте
# populate_initial_data()