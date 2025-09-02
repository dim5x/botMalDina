import logging

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.error import TimedOut
# Добавляем импорт в начале файла
from database import db_manager

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота (ЗАМЕНИТЕ НА ВАШ ТОКЕН!)
BOT_TOKEN = "8430726619:AAGqEt09f68k1iBatN35LOXPhPjbK0VTJkU"

# Состояния для ConversationHandler (добавляем к существующим)
DESCRIPTION, MEDIA, FEEDBACK = range(3)  # Обновляем range

# Добавляем новые состояния для многоуровневого меню
SELECT_SHOP, SELECT_CATEGORY, PRODUCT_QUESTION = range(3, 6)  # Продолжаем нумерацию
# Добавляем состояние для обратной связи (если не добавлено)
FEEDBACK = 6
BONUS_SCREENSHOT, BONUS_METHOD = range(7, 9)
# Обновляем главное меню (добавляем больше контекста)
MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Вопрос по товару", "Подтверждение брака"],
        ["Бонус за отзыв", "Обратная связь"]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите вариант из меню..."
)

# Клавиатура выбора магазина
SHOP_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["OZON", "WildBerries"],
        ["Назад"]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите магазин..."
)
# Клавиатура выбора категории товара
CATEGORY_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Лампы", "Массажёры"],
        ["Игрушечное оружие", "Другое"],
        ["Назад"]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите категорию..."
)

# Клавиатура для возврата
BACK_KEYBOARD = ReplyKeyboardMarkup(
    [["Назад"]],
    resize_keyboard=True
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start - приветственное сообщение и главное меню."""
    user = update.effective_user
    welcome_text = (
        f"Здравствуйте, {user.first_name}! 👋\n"
        "Я — бот техподдержки магазина MalDina.\n"
        "Чем я могу вам помочь?\n\n"
        "• Задать вопрос о товаре\n"
        "• Сообщить о проблеме/браке\n"
        "• Получить бонус за отзыв\n"
        "• Оставить обратную связь"
    )
    await update.message.reply_text(welcome_text, reply_markup=MAIN_MENU_KEYBOARD)


# Добавляем тестовую команду для проверки БД (после функции start)
# async def test_db(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Тестовая команда для проверки работы базы данных."""
#     test_message = "брак товара"
#     results = db_manager.search_faq(test_message)
#
#     if results:
#         response = "Найдены совпадения:\n\n"
#         for question, answer in results:
#             response += f"❓ {question}\n💡 {answer}\n\n"
#     else:
#         response = "По вашему запросу ничего не найдено."
#
#     await update.message.reply_text(response)


# Добавляем обработчики для кнопок меню

# async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Обрабатывает выбор пункта из главного меню."""
#     user_choice = update.message.text
#
#     if user_choice == "Подтверждение брака":
#         await start_defect_conversation(update, context)
#     elif user_choice == "Бонус за отзыв":
#         await handle_bonus_request(update, context)
#     elif user_choice == "Обратная связь":
#         await start_feedback_conversation(update, context)
#     else:
#         # Если текст не совпадает с кнопками, пытаемся найти в FAQ
#         await handle_text_message(update, context)
async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор пункта из главного меню."""
    user_choice = update.message.text

    if user_choice == "Бонус за отзыв":
        await handle_bonus_request(update, context)
    else:
        # Если текст не совпадает с кнопками, пытаемся найти в FAQ
        await handle_text_message(update, context)


async def handle_product_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик для кнопки 'Вопрос по товару'."""
    help_text = (
        "Задайте ваш вопрос о товаре. Я постараюсь найти на него ответ в нашей базе.\n\n"
        "Например, вы можете спросить:\n"
        "   • `Как получить бонус за отзыв?`\n"
        "   • `Как подтвердить брак товара?`\n"
        "   • `Какие категории товаров есть?`\n"
        # "   • Другой ваш вопрос"
    )
    await update.message.reply_text(
        help_text,
        parse_mode='MARKDOWN',
        reply_markup=ReplyKeyboardRemove()  # Убираем клавиатуру для свободного ввода
    )


async def handle_product_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог вопроса по товару с выбора магазина."""
    await update.message.reply_text(
        "🏪 <b>Выберите магазин</b>\n\n"
        "Пожалуйста, выберите магазин, в котором приобретали товар:",
        parse_mode='HTML',
        reply_markup=SHOP_KEYBOARD
    )
    return SELECT_SHOP


async def handle_shop_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор магазина."""
    shop_name = update.message.text

    if shop_name == "Назад":
        await update.message.reply_text(
            "Возвращаемся в главное меню.",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return ConversationHandler.END

    # Сохраняем выбранный магазин
    context.user_data['selected_shop'] = shop_name

    await update.message.reply_text(
        f"🏪 Выбран магазин: <b>{shop_name}</b>\n\n"
        "📦 <b>Выберите категорию товара:</b>",
        parse_mode='HTML',
        reply_markup=CATEGORY_KEYBOARD
    )
    return SELECT_CATEGORY


async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор категории товара."""
    category = update.message.text

    if category == "Назад":
        await update.message.reply_text(
            "Выберите магазин:",
            reply_markup=SHOP_KEYBOARD
        )
        return SELECT_SHOP

    # Сохраняем выбранную категорию
    context.user_data['selected_category'] = category

    await update.message.reply_text(
        f"📦 Выбрана категория: **{category}**\n\n"
        "❓ **Теперь задайте ваш вопрос о товаре:**\n\n"
        "Например:\n"
        "   • `Что такое лампа?`\n"
        # "   • `Нужно ли разрешение на игрушечное оружие?`\n"
        "   • `Какие категории товаров есть?`\n"
        "   • `Другой вопрос`",
        parse_mode='MARKDOWN',
        reply_markup=BACK_KEYBOARD
    )
    return PRODUCT_QUESTION


async def handle_product_question_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает вопрос о товаре и ищет ответ в FAQ."""
    user_question = update.message.text

    if user_question == "Назад":
        await update.message.reply_text(
            "Выберите категорию товара:",
            reply_markup=CATEGORY_KEYBOARD
        )
        return SELECT_CATEGORY

    # Добавляем контекст магазина и категории к вопросу для поиска
    shop = context.user_data.get('selected_shop', 'Не указан')
    category = context.user_data.get('selected_category', 'Не указана')

    enhanced_question = f"{user_question} {category}"
    results = db_manager.search_faq(enhanced_question)

    if results:
        # Если нашли ответы в FAQ
        response = (f"🔍 <b>Вот что я нашел по вашему вопросу:</b>\n\n"
                    f"🏪 Магазин: {shop}\n"
                    f"📦 Категория: {category}\n\n")

        for question, answer in results[:2]:  # Ограничиваем 2 результатами
            response += f"❓ <b>{question}</b>\n💡 {answer}\n\n"

        response += "Если это не ответ на ваш вопрос, попробуйте переформулировать."

        await update.message.reply_text(
            response,
            parse_mode='HTML',
            reply_markup=MAIN_MENU_KEYBOARD
        )
    else:
        # Если не нашли в FAQ
        # not_found_text = (
        #     f"❌ <b>Вопрос не найден</b>\n\n"
        #     f"🏪 Магазин: {shop}\n"
        #     f"📦 Категория: {category}\n\n"
        #     "К сожалению, я не нашел ответа на ваш вопрос в нашей базе.\n\n"
        #     "Вы можете:\n"
        #     "• Попробовать переформулировать вопрос\n"
        #     "• Обратиться к оператору через меню 'Подтверждение брака'\n"
        #     "• Выбрать другую опцию из меню"
        # )
        not_found_text = (f'Для решения вашего вопроса понадобится чуть больше времени.'
                          f'Пожалуйста, ожидайте.')
        await update.message.reply_text(
            not_found_text,
            parse_mode='HTML',
            reply_markup=MAIN_MENU_KEYBOARD
        )

    # Очищаем данные пользователя
    context.user_data.clear()
    return ConversationHandler.END


# Добавляем базовый обработчик текстовых сообщений (для FAQ)
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовые сообщения и ищет ответ в FAQ."""
    user_message = update.message.text
    print(user_message)
    results = db_manager.search_faq(user_message)
    print(results)
    if results:
        # Если нашли ответы в FAQ
        response = "🔍 <b>Вот что я нашел по вашему вопросу:</b>\n\n"
        for question, answer in results[:3]:  # Ограничиваем 3 результатами
            response += f"❓ <b>{question}</b>\n💡 {answer}\n\n"

        response += "Если это не ответило на ваш вопрос, попробуйте переформулировать или выберите другую опцию из меню."

        await update.message.reply_text(
            response,
            parse_mode='HTML',
            reply_markup=MAIN_MENU_KEYBOARD
        )
    else:
        # Если не нашли в FAQ
        not_found_text = (
            "❌ <b>Вопрос не найден</b>\n\n"
            "К сожалению, я не нашел ответа на ваш вопрос в нашей базе.\n\n"
            "Вы можете:\n"
            "• Попробовать переформулировать вопрос\n"
            "• Обратиться к оператору через меню 'Подтверждение брака'\n"
            "• Выбрать другую опцию из меню"
        )
        await update.message.reply_text(
            not_found_text,
            parse_mode='HTML',
            reply_markup=MAIN_MENU_KEYBOARD
        )


async def start_defect_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог подтверждения брака."""
    await update.message.reply_text(
        "🛠️ <b>Подтверждение брака товара</b>\n\n"
        "Для обработки вашего обращения нам потребуется дополнительная информация.\n\n"
        "Пожалуйста, подробно опишите проблему:\n"
        "   1. В чём заключается неисправность\n"
        "   2. Когда получили заказ\n"
        "   3. Был ли товар в использовании\n\n"
        "<i>Вы сможете прикрепить фото/видео на следующем шаге</i>",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardRemove()
    )
    return DESCRIPTION


async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает описание проблемы от пользователя."""
    user_description = update.message.text
    context.user_data['defect_description'] = user_description

    await update.message.reply_text(
        "📎 <b>Прикрепите медиафайлы</b>\n\n"
        "Теперь прикрепите фото или видео, на которых видна неисправность товара.\n\n"
        "<i>Если медиафайлов нет, отправьте любое текстовое сообщение для продолжения</i>",
        parse_mode='HTML'
    )
    return MEDIA


async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает медиафайлы или пропускает этот шаг."""
    if update.message.photo:
        context.user_data['defect_media'] = update.message.photo[-1].file_id
        media_type = "фото"
    elif update.message.video:
        context.user_data['defect_media'] = update.message.video.file_id
        media_type = "видео"
    elif update.message.document:
        context.user_data['defect_media'] = update.message.document.file_id
        media_type = "документ"
    else:
        context.user_data['defect_media'] = None
        media_type = None

    if media_type:
        await update.message.reply_text(f"✅ {media_type.capitalize()} получено!")

    # Сохраняем обращение в базу данных
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    description = context.user_data.get('defect_description', 'Не указано')

    db_manager.add_feedback(
        user_id=user_id,
        username=username,
        message=f"🚨 ОБРАЩЕНИЕ О БРАКЕ: {description}",
        media_type=media_type,
        media_file_id=context.user_data['defect_media']
    )

    await update.message.reply_text(
        "⏳ <b>Обращение принято!</b>\n\n"
        "Для решения вашего вопроса понадобится чуть больше времени. "
        "Пожалуйста, ожидайте. Наш оператор свяжется с вами в ближайшее время.\n\n"
        "<i>Спасибо за ваше обращение!</i>",
        parse_mode='HTML',
        reply_markup=MAIN_MENU_KEYBOARD
    )

    # Очищаем данные пользователя
    context.user_data.clear()
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help."""
    help_text = (
        "🤖 <b>Помощь по боту поддержки</b>\n\n"
        "Доступные команды:\n"
        "• /start - Запустить бота и показать главное меню\n"
        "• /help - Показать эту справку\n"
        "• /cancel - Отменить текущее действие\n\n"
        "Главное меню:\n"
        "• <b>Вопрос по товару</b> - Задать вопрос о товаре\n"
        "• <b>Подтверждение брака</b> - Сообщить о проблеме с товаром\n"
        "• <b>Бонус за отзыв</b> - Получить информацию о бонусе\n"
        "• <b>Обратная связь</b> - Оставить отзыв или предложение"
    )
    await update.message.reply_text(help_text, parse_mode='HTML')


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет текущий диалог."""
    await update.message.reply_text(
        "Диалог отменен. Возвращаемся в главное меню.",
        reply_markup=MAIN_MENU_KEYBOARD
    )
    context.user_data.clear()
    return ConversationHandler.END


def create_defect_conversation_handler():
    """Создает обработчик диалога для подтверждения брака."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Text(["Подтверждение брака"]), start_defect_conversation)
        ],
        states={
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description)
            ],
            MEDIA: [
                MessageHandler(filters.PHOTO | filters.VIDEO | filters.ATTACHMENT | filters.TEXT, handle_media)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            MessageHandler(filters.Text(["Отмена", "Назад"]), cancel_conversation)
        ],
        allow_reentry=True
    )


def create_product_question_conversation_handler():
    """Создает обработчик диалога для вопроса по товару."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Text(["Вопрос по товару"]), handle_product_question)
        ],
        states={
            SELECT_SHOP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_shop_selection)
            ],
            SELECT_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection)
            ],
            PRODUCT_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_question_text)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            MessageHandler(filters.Text(["Отмена", "Назад"]), cancel_conversation)
        ],
        allow_reentry=True
    )


# async def debug_filters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Показывает доступные атрибуты filters."""
#     import inspect
#     filter_attrs = [attr for attr in dir(filters) if not attr.startswith('_')]
#     available_filters = "\n".join(filter_attrs)
#     await update.message.reply_text(f"📋 Доступные фильтры:\n\n{available_filters}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    # Если это ошибка таймаута, логируем но не прерываем работу
    if isinstance(context.error, TimedOut):
        logger.warning("Telegram API timeout occurred, retrying...")
    else:
        # Для других ошибок можно отправить сообщение пользователю
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Произошла техническая ошибка. Пожалуйста, попробуйте позже."
            )
        except Exception:
            logger.error("Could not send error message to user")


async def start_feedback_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог обратной связи."""
    await update.message.reply_text(
        "📝 <b>Обратная связь</b>\n\n"
        "Здесь можно оставить отзыв о работе нашего магазина, "
        "чата поддержки или товара, а также рассказать о пожеланиях.\n\n"
        "Пожалуйста, напишите ваше сообщение:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardRemove()
    )
    return FEEDBACK


async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает обратную связь от пользователя."""
    feedback_text = update.message.text

    # Сохраняем обратную связь в базу данных
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    db_manager.add_feedback(
        user_id=user_id,
        username=username,
        message=f"📝 ОБРАТНАЯ СВЯЗЬ: {feedback_text}"
    )

    await update.message.reply_text(
        "✅ <b>Спасибо за вашу обратную связь!</b>\n\n"
        "Ваше сообщение сохранено и будет рассмотрено нашей командой.\n"
        "Мы ценим ваше мнение и стремимся стать лучше!",
        parse_mode='HTML',
        reply_markup=MAIN_MENU_KEYBOARD
    )

    return ConversationHandler.END


async def handle_bonus_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог получения бонуса за отзыв."""
    bonus_text = (
        "💰 <b>Бонус за отзыв</b>\n\n"
        "Уважаемый покупатель!\n"
        "Если вы остались довольны приобретенным у нас товаром, будем благодарны вашему положительному отзыву\n"
        "⭐️⭐️⭐️⭐️⭐️.\n\n"
        "<b>После публикации отзыва:</b>\n"
        "   1. Сделайте скриншот\n"
        "   2. Пришлите его в ответ на это сообщение\n"
        "   3. Укажите удобный способ получения бонуса\n\n"
        "<i>❗️ Внимание: бонусная программа доступна только для покупателей из РФ</i>\n\n"
        "Прикрепите скриншот вашего отзыва:"
    )
    await update.message.reply_text(
        bonus_text,
        parse_mode='HTML',
        reply_markup=ReplyKeyboardRemove()
    )
    return BONUS_SCREENSHOT


async def handle_bonus_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает скриншот отзыва."""
    if update.message.photo:
        # Сохраняем самое качественное фото (последнее в списке)
        context.user_data['bonus_screenshot'] = update.message.photo[-1].file_id
        await update.message.reply_text(
            "✅ Скриншот получен! Теперь укажите удобный способ получения бонуса:\n\n"
            "• Номер карты (Сбер, Тинькофф и др.)\n"
            "• Номер телефона (для Qiwi, ЮMoney)\n"
            "• Другой способ",
            reply_markup=ReplyKeyboardMarkup(
                [["Назад"]],
                resize_keyboard=True
            )
        )
        return BONUS_METHOD

    elif update.message.document:
        # Обработка документа (если скриншот отправлен как файл)
        context.user_data['bonus_screenshot'] = update.message.document.file_id
        context.user_data['screenshot_type'] = 'document'
        await update.message.reply_text(
            "✅ Файл получен! Теперь укажите удобный способ получения бонуса...",
            reply_markup=ReplyKeyboardMarkup(
                [["Назад"]],
                resize_keyboard=True
            )
        )
        return BONUS_METHOD

    else:
        await update.message.reply_text(
            "📎 Пожалуйста, прикрепите скриншот отзыва как фото или документ.\n"
            "Если у вас нет скриншота, напишите 'назад' для возврата в меню."
        )
        return BONUS_SCREENSHOT


async def handle_bonus_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает способ получения бонуса."""
    bonus_method = update.message.text

    if bonus_method == "Назад":
        await update.message.reply_text(
            "Возвращаемся к загрузке скриншота...",
            reply_markup=ReplyKeyboardRemove()
        )
        return BONUS_SCREENSHOT

    # Сохраняем способ получения бонуса
    context.user_data['bonus_method'] = bonus_method

    # Сохраняем заявку в базу данных
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    screenshot_id = context.user_data.get('bonus_screenshot', 'Нет скриншота')
    method = context.user_data.get('bonus_method', 'Не указан')

    db_manager.add_feedback(
        user_id=user_id,
        username=username,
        message=f"💰 ЗАЯВКА НА БОНУС: Способ получения - {method} | Скриншот: {screenshot_id}",
        media_file_id=screenshot_id,
        media_type="screenshot",
    )

    await update.message.reply_text(
        "🎉 <b>Заявка на бонус принята!</b>\n\n"
        "Ваша заявка на получение бонуса за отзыв успешно отправлена.\n\n"
        "<b>Детали заявки:</b>\n"
        f"• Способ получения: {bonus_method}\n\n"
        "Наш менеджер обработает вашу заявку в ближайшее время и свяжется с вами для уточнения деталей.\n\n"
        "<i>Спасибо за ваш отзыв!</i>",
        parse_mode='HTML',
        reply_markup=MAIN_MENU_KEYBOARD
    )

    # Очищаем данные пользователя
    context.user_data.clear()
    return ConversationHandler.END


def create_bonus_conversation_handler():
    """Создает обработчик диалога для бонуса за отзыв."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Text(["Бонус за отзыв"]), handle_bonus_request)
        ],
        states={
            BONUS_SCREENSHOT: [
                MessageHandler(filters.PHOTO | filters.ATTACHMENT | filters.TEXT, handle_bonus_screenshot)
            ],
            BONUS_METHOD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bonus_method)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            MessageHandler(filters.Text(["Отмена", "Назад"]), cancel_conversation)
        ],
        allow_reentry=True
    )


def create_feedback_conversation_handler():
    """Создает обработчик диалога для обратной связи."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Text(["Обратная связь"]), start_feedback_conversation)
        ],
        states={
            FEEDBACK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
            MessageHandler(filters.Text(["Отмена", "Назад"]), cancel_conversation)
        ],
        allow_reentry=True
    )


def main() -> None:
    """Основная функция запуска бота."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_conversation))
    # application.add_handler(CommandHandler("test_db", test_db))

    # Добавляем ConversationHandler'ы
    application.add_handler(create_defect_conversation_handler())
    application.add_handler(create_product_question_conversation_handler())
    application.add_handler(create_feedback_conversation_handler())
    application.add_handler(create_bonus_conversation_handler())  # ← Новый обработчик

    # Убираем старый обработчик для "Бонус за отзыв", так как теперь это ConversationHandler

    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text_message
    ))

    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)

    logger.info("Бот запущен и готов к работе!")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
