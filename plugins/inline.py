import logging
from urllib.parse import quote

from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultCachedDocument

from utils import get_search_results
from info import CACHE_TIME, SHARE_BUTTON_TEXT, AUTH_USERS, AUTH_CHANNEL

logger = logging.getLogger(__name__)
cache_time = 0 if AUTH_USERS or AUTH_CHANNEL else CACHE_TIME

@Client.on_inline_query(filters.user(AUTH_USERS) if AUTH_USERS else None)
async def answer(bot, query):
    if AUTH_CHANNEL and not await is_subscribed(bot, query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text='You have to subscribe the channel ✔',
            switch_pm_parameter="subscribe",
        )
        return

    # --- Safely split query ---
    text = query.query.strip()
    file_type = None
    if '|' in text:
        parts = text.split('|', maxsplit=1)
        text = parts[0].strip()
        file_type = parts[1].strip().lower() if len(parts) > 1 else None

    offset = int(query.offset or 0)
    reply_markup = get_reply_markup(bot.username, query=text)
    files, next_offset = await get_search_results(text, file_type=file_type, max_results=10, offset=offset)

    results = []
    for file in files:
        # Escape filename + size
        safe_file_name = escape_html(file.file_name)
        safe_file_size = escape_html(size_formatter(file.file_size))

        caption = (
            "<b>| Kuttu Bot 2 ™ |</b>\n"
            f"📁 <b>File Name:</b> {safe_file_name}\n"
            f"📦 <b>File Size:</b> {safe_file_size}\n\n"
            "Free Movie Group 🎬 <a href='https://t.me/wudixh'>@wudixh</a>"
        )

        # Ensure caption <= 1024 characters
        if len(caption) > 1024:
            caption = caption[:1020] + "..."

        results.append(
            InlineQueryResultCachedDocument(
                title=file.file_name,
                document_file_id=file.file_id,
                caption=caption,
                parse_mode="HTML",
                description=f"Size: {size_formatter(file.file_size)} | Type: {file.file_type} | © Kuttu Bot 2 ™",
                reply_markup=reply_markup
            )
        )

    await query.answer(
        results=results,
        cache_time=cache_time,
        switch_pm_text=f"📁Results📁 for {text}" if results else f"❌No Results❌ for {text}",
        switch_pm_parameter="start" if results else "okay",
        next_offset=str(next_offset) if results else ""
    )

def get_reply_markup(username, query):
    url = 'https://t.me/share/url?url=' + quote(SHARE_BUTTON_TEXT.format(username=username))
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Search again 🔎', switch_inline_query_current_chat=query),
            InlineKeyboardButton('Share bot 💕', url=url)
        ],
        [InlineKeyboardButton('Developer 😎', url="https://telegram.dog/wudixh13/4")]
    ])

def size_formatter(size):
    units = ["Bytes", "KB", "MB", "GB", "TB"]
    size = float(size)
    i = 0
    while size >= 1024 and i < len(units)-1:
        size /= 1024
        i += 1
    return "%.2f %s" % (size, units[i])

def escape_html(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))

async def is_subscribed(bot, query):
    try:
        user = await bot.get_chat_member(AUTH_CHANNEL, query.from_user.id)
        if user.status != 'kicked':
            return True
    except UserNotParticipant:
        pass
    except Exception as e:
        logger.exception(e)
    return False
