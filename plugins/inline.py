import logging
from urllib.parse import quote

from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultCachedDocument
from pyrogram.enums import ParseMode

from utils import get_search_results
from info import CACHE_TIME, SHARE_BUTTON_TEXT, AUTH_USERS, AUTH_CHANNEL

logger = logging.getLogger(__name__)
cache_time = 0 if AUTH_USERS or AUTH_CHANNEL else CACHE_TIME


@Client.on_inline_query(filters.user(AUTH_USERS) if AUTH_USERS else None)
async def answer(bot, query):
    """Show search results for given inline query"""

    if AUTH_CHANNEL and not await is_subscribed(bot, query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text='You have to subscribe the channel ✔',
            switch_pm_parameter="subscribe",
        )
        return

    results = []
    if '|' in query.query:
        text, file_type = query.query.split('|', maxsplit=1)
        text = text.strip()
        file_type = file_type.strip().lower()
    else:
        text = query.query.strip()
        file_type = None

    offset = int(query.offset or 0)
    reply_markup = get_reply_markup(bot.username, query=text)
    files, next_offset = await get_search_results(text, file_type=file_type, max_results=10, offset=offset)

    for file in files:
        safe_name = escape_html(file.file_name[:100])
        safe_size = escape_html(size_formatter(file.file_size))
        safe_type = escape_html((file.file_type or "")[:50])

        caption_body = (
            f"📁 <b>File Name:</b> {safe_name}\n"
            f"📦 <b>File Size:</b> {safe_size}\n\n"
            "Free Movie Group 🎬 <a href='https://t.me/wudixh'>@wudixh</a>"
        )

        caption = f"<b>| Kuttu Bot 2 ™ |</b>\n{caption_body}"

        if len(caption) > 1024:
            # Safely truncate body text (before tags)
            caption_body = caption_body[:1000]
            caption = f"<b>| Kuttu Bot 2 ™ |</b>\n{caption_body}"

        results.append(
            InlineQueryResultCachedDocument(
                title=file.file_name[:64],  # Telegram title limit
                document_file_id=file.file_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                description=f"Size: {size_formatter(file.file_size)} | Type: {safe_type}",
                reply_markup=reply_markup
            )
        )

    await query.answer(
        results=results or [],
        cache_time=cache_time,
        switch_pm_text="📁Results📁" if results else "❌No Results❌",
        switch_pm_parameter="start" if results else "okay",
        next_offset=str(next_offset) if results else ""
    )


def get_reply_markup(username, query):
    url = 'https://t.me/share/url?url=' + quote(SHARE_BUTTON_TEXT.format(username=username))
    buttons = [
        [
            InlineKeyboardButton('Search again 🔎', switch_inline_query_current_chat=query),
            InlineKeyboardButton('Share bot 💕', url=url)
        ],
        [
            InlineKeyboardButton('Developer 😎', url="https://telegram.dog/wudixh13/4")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def size_formatter(size):
    """Get size in readable format"""
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units) - 1:
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])


def escape_html(text):
    """Escape characters for HTML"""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            )


async def is_subscribed(bot, query):
    try:
        user = await bot.get_chat_member(AUTH_CHANNEL, query.from_user.id)
    except UserNotParticipant:
        return False
    except Exception as e:
        logger.exception(e)
        return False
    else:
        return user.status != 'kicked'
