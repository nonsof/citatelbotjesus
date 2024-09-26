import logging
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Настройки
TELEGRAM_TOKEN = "7015334956:AAEjtyg7x4qzOotRxOBED5_CxGY9Fzb0Xnc"
GOOGLE_SHEET_ID = "1U3DJ-I6WOAcwW-J-j2p0bpH34c0vD-mjK6uresaj9Zg"
CHAT_ID = -1002045032457  # Используем только один фиксированный ID чата

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Настройка Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet("ДР")

# Настройка бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()


# Функция для получения дней рождений на сегодня
def get_birthdays_today():
    today = datetime.now().strftime("%d-%m")
    birthdays_today = []
    records = sheet.get_all_records()

    for record in records:
        bday_str = record.get("Дата")
        if isinstance(bday_str, str):
            try:
                bday = datetime.strptime(bday_str, "%d-%m").strftime("%d-%m")
                if bday == today:
                    name = record[
                        "Имя"
                    ]  # Убираем upper(), чтобы оставить исходное написание
                    tag = record.get("тэг")
                    if tag:
                        birthdays_today.append(f"{name} (@{tag})")
                    else:
                        birthdays_today.append(name)
            except ValueError:
                continue
        else:
            continue

    return birthdays_today


# Функция для получения всех дней рождений
def get_all_birthdays():
    records = sheet.get_all_records()
    all_birthdays = []
    for record in records:
        name = record["Имя"]  # Убираем upper(), чтобы оставить исходное написание
        tag = record.get("тэг")
        if tag:
            all_birthdays.append(f"{name} (@{tag}): {record['Дата']}")
        else:
            all_birthdays.append(f"{name}: {record['Дата']}")
    return all_birthdays


# Функция для ежедневного уведомления о днях рождения
async def daily_check():
    birthdays = get_birthdays_today()
    if birthdays:
        message_text = "Сегодня день рождения у:\n" + "\n".join(birthdays)
    else:
        message_text = "Сегодня никого не поздравляем."

    # Отправляем сообщение в указанный чат
    try:
        await bot.send_message(CHAT_ID, message_text)
        logging.info(f"Сообщение отправлено в чат {CHAT_ID}")
    except Exception as e:
        logging.error(f"Не удалось отправить сообщение в чат {CHAT_ID}: {e}")


# Функция для еженедельного оповещения о встрече
async def weekly_meeting_reminder():
    message_text = "Через 5 минут начинается еженедельный синх, ждём всех в дискорде https://discord.com/channels/1201431411538796586/1201431412662874235"

    # Отправляем сообщение в указанный чат
    try:
        await bot.send_message(CHAT_ID, message_text)
        logging.info(f"Сообщение отправлено в чат {CHAT_ID} с напоминанием о встрече")
    except Exception as e:
        logging.error(f"Не удалось отправить сообщение в чат {CHAT_ID}: {e}")


# Обработка команды /start
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="Показать всех дней рождений")
    builder.button(text="Проверить дни рождения сегодня")
    markup = builder.as_markup(resize_keyboard=True)

    await message.answer(
        "Привет! Я могу напоминать о днях рождениях и встречах. Используйте кнопки ниже:",
        reply_markup=markup,
    )


# Обработка запроса на проверку дней рождений сегодня
@router.message(lambda m: m.text == "Проверить дни рождения сегодня")
async def check_today_birthdays(message: types.Message):
    birthdays = get_birthdays_today()
    if birthdays:
        message_text = "Сегодня день рождения у:\n" + "\n".join(birthdays)
    else:
        message_text = "Сегодня никого не поздравляем."
    await message.answer(message_text)


# Обработка запроса на показ всех дней рождений
@router.message(lambda m: m.text == "Показать всех дней рождений")
async def show_all_birthdays(message: types.Message):
    all_birthdays = get_all_birthdays()
    if all_birthdays:
        message_text = "Список всех дней рождений:\n" + "\n".join(all_birthdays)
    else:
        message_text = "Нет доступных данных о днях рождениях."
    await message.answer(message_text)


# Основная функция запуска бота и планировщика задач
async def main():
    # Устанавливаем маршрутизатор
    dp.include_router(router)

    # Настройка планировщика
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        daily_check, CronTrigger(hour=10, minute=00)
    )  # Ежедневное оповещение о днях рождения в 9:00
    scheduler.add_job(
        weekly_meeting_reminder, CronTrigger(day_of_week="mon", hour=18, minute=25)
    )  # Еженедельное оповещение о встрече в понедельник в 18:30
    scheduler.start()

    # Запуск polling с указанием экземпляра бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
