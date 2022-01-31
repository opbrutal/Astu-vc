from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_NAME as bn
from helpers.filters import other_filters2
from time import time
from datetime import datetime
from helpers.decorators import authorized_users_only
from config import BOT_NAME

START_TIME = datetime.utcnow()
START_TIME_ISO = START_TIME.replace(microsecond=0).isoformat()
TIME_DURATION_UNITS = (
    ("week", 60 * 60 * 24 * 7),
    ("day", 60 ** 2 * 24),
    ("hour", 60 ** 2),
    ("min", 60),
    ("sec", 1),
)


async def _human_time_duration(seconds):
    if seconds == 0:
        return "inf"
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append("{} {}{}".format(amount, unit, "" if amount == 1 else "s"))
    return ", ".join(parts)


@Client.on_message(other_filters2)
async def start(_, message: Message):
      await message.reply_sticker("CAACAgQAAx0CW21HzQACuGVh93MBKwfpf1KoLJtVbt3h7oRdewACugADBxSGHzhRIJtPw0ksIwQ")
      await message.reply_text(
       f"""**Hᴇʏ ɪᴛs {bn}** \n
**I ᴀᴍ ʟᴀᴢʏ Aʙᴏᴜᴛ ᴛʏᴘɪɴɢ ..ɪᴛᴢ ᴀ ʙᴏᴛ ᴍᴀᴅᴇ ғᴏʀ ᴘʟᴀʏ ᴍᴜsɪᴄ ɪɴ ᴠᴄ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ ʟᴀɢ & ᴅᴇʟᴀʏ.😈❣️
Dᴇᴠᴇʟᴏᴘᴇᴅ Bʏ : [𝙰𝚂𝚃𝚄](https://t.me/astu_backk)**
        """,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                         " ᴏᴡɴᴇʀ ", url="https://t.me/astu_backk")
                  ],[
                    InlineKeyboardButton(
                        "😈  ɢʀᴏᴜᴘ", url="https://t.me/shivamdemon"
                    ),
                    InlineKeyboardButton(
                        "✌️ sᴜᴘᴘᴏʀᴛ", url="https://t.me/w2h_op"
                    )
                ],[ 
                    InlineKeyboardButton(
                        "➕ ɢᴇᴛ ᴍᴇ ᴛᴏ ᴜʀ ɢʀᴏᴜᴘ➕", url="https://t.me/LEGEND_ALONE_MUSIC_BOT?startgroup=true"
                    )]
            ]
        ),
     disable_web_page_preview=True
    )

@Client.on_message(filters.command("start") & ~filters.private & ~filters.channel)
async def gstart(_, message: Message):
      await message.reply_text("""** ʙᴏᴛ ᴀᴄᴛɪᴠᴇ ᴅᴇᴀʀ ᴅᴏɴᴛ ᴡᴏʀʀʏ ✅**""",
      reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔊 ᴇɴᴄᴏᴅᴇᴅ ʙʏ", url="https://t.me/shivamdemon")
                ]
            ]
        )
   )


