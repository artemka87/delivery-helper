"""Telegram-бот для расчёта стоимости доставки из Ростова-на-Дону.

Токен бота загружается только из локального файла .env и не хранится в коде.
"""

import logging
import math
import os
from typing import Final

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from delivery_helper.calculator import (
    DISTANCES_KM,
    TARIFFS,
    DeliveryError,
    calculate_delivery,
    find_city,
)

CITY, WEIGHT, TARIFF, NEXT_ACTION = range(4)
NEW_CALCULATION: Final = "Новый расчёт"
FINISH: Final = "Завершить"

logger = logging.getLogger(__name__)


def cities_keyboard() -> ReplyKeyboardMarkup:
    """Создаёт клавиатуру с поддерживаемыми городами назначения."""
    cities = [city for city in DISTANCES_KM if city != "Ростов-на-Дону"]
    rows = [cities[index:index + 2] for index in range(0, len(cities), 2)]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)


def tariffs_keyboard() -> ReplyKeyboardMarkup:
    """Создаёт клавиатуру выбора тарифа."""
    return ReplyKeyboardMarkup([list(TARIFFS)], resize_keyboard=True, one_time_keyboard=True)


def next_action_keyboard() -> ReplyKeyboardMarkup:
    """Создаёт клавиатуру после готового расчёта."""
    return ReplyKeyboardMarkup(
        [[NEW_CALCULATION, FINISH]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def parse_weight(text: str) -> float:
    """Преобразует вес в число, принимая десятичную запятую."""
    try:
        weight = float(text.strip().replace(",", "."))
    except ValueError as error:
        raise ValueError("Введите вес числом, например: 2 или 2,5.") from error

    if not math.isfinite(weight):
        raise ValueError("Введите вес обычным числом, например: 2 или 2,5.")

    return weight


def format_result(result: dict) -> str:
    """Форматирует словарь результата калькулятора для сообщения Telegram."""
    weight = f"{result['weight_kg']:g}".replace(".", ",")
    days = result["days"]
    day_word = "день" if days == 1 else "дня" if 2 <= days <= 4 else "дней"

    return (
        "<b>Расчёт готов</b> 📦\n\n"
        f"<b>Направление:</b> Ростов-на-Дону → {result['city']}\n"
        f"<b>Расстояние:</b> {result['distance_km']} км\n"
        f"<b>Вес:</b> {weight} кг\n"
        f"<b>Тариф:</b> {result['tariff']}\n\n"
        f"<b>Стоимость:</b> {result['price']} руб.\n"
        f"<b>Срок доставки:</b> {days} {day_word}"
    )


def cities_text() -> str:
    """Возвращает список поддерживаемых городов."""
    cities = [city for city in DISTANCES_KM if city != "Ростов-на-Дону"]
    return "Поддерживаемые города:\n" + "\n".join(f"• {city}" for city in cities)


def current_state(context: ContextTypes.DEFAULT_TYPE) -> int:
    """Возвращает сохранённый шаг диалога для команд внутри сценария."""
    return context.user_data.get("state", CITY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает новый расчёт."""
    context.user_data.clear()
    context.user_data["state"] = CITY
    await update.message.reply_text(
        "Привет! Я помогу рассчитать стоимость и срок доставки из Ростова-на-Дону.\n\n"
        "Выбери город на клавиатуре или напиши его вручную.",
        reply_markup=cities_keyboard(),
    )
    return CITY


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает инструкцию вне активного диалога."""
    await update.message.reply_text(
        "Я рассчитываю стоимость и срок доставки из Ростова-на-Дону.\n\n"
        "1. Нажми /start\n"
        "2. Выбери город\n"
        "3. Укажи вес посылки в килограммах\n"
        "4. Выбери тариф\n\n"
        "Вес можно вводить с запятой: 2,5.\n"
        "Команда /cities покажет список городов.",
    )


async def conversation_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает инструкцию и сохраняет текущий шаг диалога."""
    await help_command(update, context)
    return current_state(context)


async def cities_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает список городов вне активного диалога."""
    await update.message.reply_text(cities_text())


async def conversation_cities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает города и сохраняет текущий шаг диалога."""
    await cities_command(update, context)
    return current_state(context)


async def receive_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Проверяет город и переходит к вводу веса."""
    city_text = update.message.text
    try:
        city = find_city(city_text)
    except DeliveryError:
        await update.message.reply_text(
            f"Город «{city_text.strip()}» пока не поддерживается.\n"
            "Выбери город на клавиатуре или посмотри список командой /cities.",
            reply_markup=cities_keyboard(),
        )
        return CITY

    context.user_data["city"] = city
    context.user_data["state"] = WEIGHT
    await update.message.reply_text(
        f"Отлично, направление: Ростов-на-Дону → {city}.\n\n"
        "Теперь укажи вес посылки в килограммах. Например: 2 или 2,5.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return WEIGHT


async def receive_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Проверяет вес и предлагает выбрать тариф."""
    try:
        weight = parse_weight(update.message.text)
        # Проверяем вес через расчётное ядро, чтобы правила не дублировались в боте.
        calculate_delivery(context.user_data["city"], weight)
    except (ValueError, DeliveryError) as error:
        await update.message.reply_text(f"{error}\nПопробуй ещё раз.")
        return WEIGHT

    context.user_data["weight"] = weight
    context.user_data["state"] = TARIFF
    await update.message.reply_text(
        "Выбери тариф доставки:",
        reply_markup=tariffs_keyboard(),
    )
    return TARIFF


async def receive_tariff(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выполняет расчёт и отправляет результат."""
    tariff = update.message.text
    try:
        result = calculate_delivery(
            context.user_data["city"],
            context.user_data["weight"],
            tariff,
        )
    except DeliveryError as error:
        await update.message.reply_text(f"{error}\nВыбери тариф на клавиатуре.")
        return TARIFF

    context.user_data["state"] = NEXT_ACTION
    await update.message.reply_text(
        format_result(result),
        parse_mode="HTML",
        reply_markup=next_action_keyboard(),
    )
    return NEXT_ACTION


async def receive_next_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает новый расчёт или завершает сценарий."""
    action = update.message.text
    if action == NEW_CALCULATION:
        return await start(update, context)

    if action == FINISH:
        context.user_data.clear()
        await update.message.reply_text(
            "Расчёт завершён. Когда понадобится — нажми /start.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    await update.message.reply_text("Выбери «Новый расчёт» или «Завершить» на клавиатуре.")
    return NEXT_ACTION


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет текущий расчёт."""
    context.user_data.clear()
    await update.message.reply_text(
        "Расчёт отменён. Чтобы начать заново, нажми /start.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Логирует непредвиденные ошибки и отвечает нейтральным сообщением."""
    logger.exception("Необработанная ошибка в Telegram-боте", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Что-то пошло не так. Попробуй повторить расчёт с /start."
            )
        except Exception:  # Telegram может быть временно недоступен.
            logger.exception("Не удалось отправить сообщение об ошибке")


def create_application(token: str) -> Application:
    """Создаёт приложение Telegram и регистрирует обработчики."""
    private_text = filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE
    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start, filters=filters.ChatType.PRIVATE)],
        states={
            CITY: [MessageHandler(private_text, receive_city)],
            WEIGHT: [MessageHandler(private_text, receive_weight)],
            TARIFF: [MessageHandler(private_text, receive_tariff)],
            NEXT_ACTION: [MessageHandler(private_text, receive_next_action)],
        },
        fallbacks=[
            CommandHandler("start", start, filters=filters.ChatType.PRIVATE),
            CommandHandler("help", conversation_help, filters=filters.ChatType.PRIVATE),
            CommandHandler("cities", conversation_cities, filters=filters.ChatType.PRIVATE),
            CommandHandler("cancel", cancel, filters=filters.ChatType.PRIVATE),
        ],
    )

    application = ApplicationBuilder().token(token).build()
    application.add_handler(conversation)
    application.add_handler(CommandHandler("help", help_command, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("cities", cities_command, filters=filters.ChatType.PRIVATE))
    application.add_error_handler(error_handler)
    return application


def main() -> None:
    """Загружает токен и запускает long polling."""
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN не задан. Создай .env по примеру .env.example "
            "и добавь туда токен от BotFather."
        )

    logging.basicConfig(
        format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
        level=logging.INFO,
    )
    logger.info("Бот запущен через long polling")
    create_application(token).run_polling()


if __name__ == "__main__":
    main()
