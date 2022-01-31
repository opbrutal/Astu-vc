import os
from os import path
from typing import Callable
from pyrogram import Client, filters
from pyrogram.types import Message, Voice, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserAlreadyParticipant
from Client import callsmusic, queues
from Client.callsmusic import client as USER
from helpers.admins import get_administrators
import requests
import aiohttp
import yt_dlp
from youtube_search import YoutubeSearch
import converter
from youtube import youtube
from config import DURATION_LIMIT, que, SUDO_USERS
from cache.admins import admins as a
from helpers.filters import command
from helpers.decorators import errors, authorized_users_only
from helpers.errors import DurationLimitError
from helpers.gets import get_url, get_file_name
from helpers.channelmusic import get_chat_id
import aiofiles
import ffmpeg
from PIL import Image, ImageFont, ImageDraw
from pytgcalls import StreamType
from pytgcalls.types.input_stream import InputAudioStream
from pytgcalls.types.input_stream import InputStream


aiohttpsession = aiohttp.ClientSession()
chat_id = None
arq = ARQ("https://thearq.tech", ARQ_API_KEY, aiohttpsession)
DISABLED_GROUPS = []
useer = "NaN"


def cb_admin_check(func: Callable) -> Callable:
    async def decorator(client, cb):
        admemes = a.get(cb.message.chat.id)
        if cb.from_user.id in admemes:
            return await func(client, cb)
        else:
            await cb.answer("You ain't allowed!", show_alert=True)
            return

    return decorator


def transcode(filename):
    ffmpeg.input(filename).output(
        "input.raw", 
        format="s16le", 
        acodec="pcm_s16le", 
        ac=2, 
        ar="48k"
    ).overwrite_output().run()
    os.remove(filename)


# Convert seconds to mm:ss
def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)


# Convert hh:mm:ss to seconds
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


# Change image size
def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


async def generate_cover(requested_by, title, views, duration, thumbnail):
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open("background.png", mode="wb")
                await f.write(await resp.read())
                await f.close()

    image1 = Image.open("./background.png")
    image2 = Image.open("./etc/foreground_square.png")
    image3 = changeImageSize(1280, 720, image1)
    image4 = changeImageSize(1280, 720, image2)
    image5 = image3.convert("RGBA")
    image6 = image4.convert("RGBA")
    Image.alpha_composite(image5, image6).save("temp.png")
    img = Image.open("temp.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("etc/font.otf", 32)
    draw.text((205, 550), f"Title: {title}", (51, 215, 255), font=font)
    draw.text((205, 590), f"Duration: {duration}", (255, 255, 255), font=font)
    draw.text((205, 630), f"Views: {views}", (255, 255, 255), font=font)
    draw.text(
        (205, 670),
        f"Added By: {requested_by}",
        (255, 255, 255),
        font=font,
    )
    img.save("final.png")
    os.remove("temp.png")
    os.remove("background.png")


@Client.on_message(filters.command("playlist") & filters.group & ~filters.edited)
async def playlist(client, message):
    global que
    if message.chat.id in DISABLED_GROUPS:
        return
    queue = que.get(message.chat.id)
    if not queue:
        await message.reply_text("Player is idle")
    temp = []
    for t in queue:
        temp.append(t)
    now_playing = temp[0][0]
    by = temp[0][1].mention(style="md")
    msg = "**Now Playing** in {}".format(message.chat.title)
    msg += "\n- " + now_playing
    msg += "\n- Req by " + by
    temp.pop(0)
    if temp:
        msg += "\n\n"
        msg += "**Queue**"
        for song in temp:
            name = song[0]
            usr = song[1].mention(style="md")
            msg += f"\n- {name}"
            msg += f"\n- Req by {usr}\n"
    await message.reply_text(msg)


# ============================= Settings =========================================


def updated_stats(chat, queue, vol=200):
    if chat.id in callsmusic.active_chats:
        # if chat.id in active_chats:
        stats = "Settings of **{}**".format(chat.title)
        if len(que) > 0:
            stats += "\n\n"
            stats += "Volume : {}%\n".format(vol)
            stats += "Songs in queue : `{}`\n".format(len(que))
            stats += "Now Playing : **{}**\n".format(queue[0][0])
            stats += "Requested by : {}".format(queue[0][1].mention)
    else:
        stats = None
    return stats


def r_ply(type_):
    if type_ == "play":
        pass
    else:
        pass
    mar = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏹", "leave"),
                InlineKeyboardButton("⏸", "puse"),
                InlineKeyboardButton("▶️", "resume"),
                InlineKeyboardButton("⏭", "skip"),
            ],
            [
                InlineKeyboardButton("Playlist 📖", "playlist"),
            ],
            [InlineKeyboardButton("🗑️", "cls")],
        ]
    )
    return mar


@Client.on_message(filters.command("current") & filters.group & ~filters.edited)
async def ee(client, message):
    if message.chat.id in DISABLED_GROUPS:
        return
    queue = que.get(message.chat.id)
    stats = updated_stats(message.chat, queue)
    if stats:
        await message.reply(stats)
    else:
        await message.reply("𝐕𝐜 𝐍𝐨𝐭 𝐒𝐭𝐚𝐫𝐭𝐞𝐝 𝐘𝐞𝐭")


@Client.on_message(filters.command("player") & filters.group & ~filters.edited)
@authorized_users_only
async def settings(client, message):
    if message.chat.id in DISABLED_GROUPS:
        await message.reply("𝐌𝐮𝐬𝐢𝐜 𝐏𝐥𝐚𝐲𝐞𝐫 𝐈𝐬 𝐝𝐢𝐬𝐚𝐛𝐥𝐞𝐝")
        return
    playing = None
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.active_chats:
        playing = True
    queue = que.get(chat_id)
    stats = updated_stats(message.chat, queue)
    if stats:
        if playing:
            await message.reply(stats, reply_markup=r_ply("pause"))
        else:
            await message.reply(stats, reply_markup=r_ply("play"))
    else:
        await message.reply("𝐕𝐜 𝐍𝐨𝐭 𝐒𝐭𝐚𝐫𝐭𝐞𝐝 𝐘𝐞𝐭")


@Client.on_message(
    filters.command("musicplayer") & ~filters.edited & ~filters.bot & ~filters.private
)
@authorized_users_only
async def hfmm(_, message):
    global DISABLED_GROUPS
    try:
        message.from_user.id
    except:
        return
    if len(message.command) != 2:
        await message.reply_text(
            "𝐈 𝐑𝐞𝐜𝐨𝐠𝐧𝐢𝐳𝐞  `/musicplayer on` & /musicplayer `off` 𝐨𝐧𝐥𝐲"
        )
        return
    status = message.text.split(None, 1)[1]
    message.chat.id
    if status == "ON" or status == "on" or status == "On":
        lel = await message.reply("`Processing...`")
        if not message.chat.id in DISABLED_GROUPS:
            await lel.edit("𝐌𝐮𝐬𝐢𝐜 𝐏𝐥𝐚𝐲𝐞𝐫 𝐈𝐬 𝐚𝐥𝐫𝐞𝐚𝐝𝐲  𝐀𝐜𝐭𝐢𝐯𝐚𝐭𝐞𝐝")
            return
        DISABLED_GROUPS.remove(message.chat.id)
        await lel.edit(
            f"Music Player Successfully Enabled For Users In The Chat {message.chat.id}"
        )

    elif status == "OFF" or status == "off" or status == "Off":
        lel = await message.reply("`Processing...`")

        if message.chat.id in DISABLED_GROUPS:
            await lel.edit("𝐌𝐮𝐬𝐢𝐜 𝐏𝐥𝐚𝐲𝐞𝐫 𝐈𝐬 𝐀𝐥𝐫𝐞𝐚𝐝𝐲 𝐃𝐞𝐚𝐜𝐭𝐢𝐯𝐚𝐭𝐞𝐝")
            return
        DISABLED_GROUPS.append(message.chat.id)
        await lel.edit(
            f"Music Player Successfully Deactivated For Users In The Chat {message.chat.id}"
        )
    else:
        await message.reply_text(
            "𝐈 𝐑𝐞𝐜𝐨𝐠𝐧𝐢𝐳𝐞  `/musicplayer on` & /musicplayer `off` 𝐨𝐧𝐥𝐲"
        )


@Client.on_callback_query(filters.regex(pattern=r"^(playlist)$"))
async def p_cb(b, cb):
    global que
    que.get(cb.message.chat.id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    cb.message.chat
    cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("𝐏𝐥𝐚𝐲𝐞𝐫 𝐈𝐬 𝐈𝐝𝐥𝐞")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "<b>𝐍𝐨𝐰 𝐏𝐥𝐚𝐲𝐢𝐧𝐠</b> in {}".format(cb.message.chat.title)
        msg += "\n- " + now_playing
        msg += "\n- 𝐑𝐞𝐪. 𝐁𝐲 " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**𝐐𝐮𝐞𝐮𝐞 𝐀𝐭 **"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n- {name}"
                msg += f"\n- 𝐑𝐞𝐪. 𝐁𝐲 {usr}\n"
        await cb.message.edit(msg)


@Client.on_callback_query(
    filters.regex(pattern=r"^(play|pause|skip|leave|puse|resume|menu|cls)$")
)
@cb_admin_check
async def m_cb(b, cb):
    global que
    if (
        cb.message.chat.title.startswith("Channel Music: ")
        and chat.title[14:].isnumeric()
    ):
        chet_id = int(chat.title[13:])
    else:
        chet_id = cb.message.chat.id
    qeue = que.get(chet_id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    m_chat = cb.message.chat

    the_data = cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "pause":
        (
            await cb.answer("Music Paused!")
        ) if (
            callsmusic.pause(chet_id)
        ) else (
            await cb.answer("Chat is not connected!", show_alert=True)
        )
        await cb.message.edit(updated_stats(m_chat, qeue), reply_markup=r_ply("play"))

    elif type_ == "resume":
        (
            await cb.answer("Music Resumed!")
        ) if (
            callsmusic.resume(chet_id)
        ) else (
            await cb.answer("Chat is not connected!", show_alert=True)
        )
        await cb.message.edit(updated_stats(m_chat, qeue), reply_markup=r_ply("pause"))

    elif type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("Player is idle")
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**𝐍𝐨𝐰 𝐏𝐥𝐚𝐲𝐢𝐧𝐠** in {}".format(cb.message.chat.title)
        msg += "\n- " + now_playing
        msg += "\n- 𝐑𝐞𝐪. 𝐁𝐲 " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**𝐐𝐮𝐞𝐮𝐞**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n- {name}"
                msg += f"\n- 𝐑𝐞𝐪 𝐁𝐲. {usr}\n"
        await cb.message.edit(msg)

    elif type_ == "resume":
        (
            await cb.answer("𝐑𝐞𝐬𝐮𝐦𝐞𝐝!")
        ) if (
            callsmusic.resume(chet_id)
        ) else (
            await cb.answer("Chat is not connected or already playng", show_alert=True)
        )
            
    elif type_ == "pause":
        (
            await cb.answer("𝐏𝐚𝐮𝐬𝐞𝐝!")
        ) if (
            callsmusic.pause(chet_id)
        ) else (
            await cb.answer("Chat is not connected or already paused", show_alert=True)
        )
            
    elif type_ == "cls":
        await cb.answer("Closed menu")
        await cb.message.delete()

    elif type_ == "menu":
        stats = updated_stats(cb.message.chat, qeue)
        await cb.answer("Menu opened")
        marr = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⏹", "leave"),
                    InlineKeyboardButton("⏸", "puse"),
                    InlineKeyboardButton("▶️", "resume"),
                    InlineKeyboardButton("⏭", "skip"),
                ],
                [
                    InlineKeyboardButton("Playlist", "playlist"),
                ],
                [InlineKeyboardButton("🗑️", "cls")],
            ]
        )
        await cb.message.edit(stats, reply_markup=marr)
        
    elif type_ == "skip":
        if qeue:
            qeue.pop(0)
        if chet_id not in callsmusic.active_chats:
            await cb.answer("Chat is not connected!", show_alert=True)
        else:
            queues.task_done(chet_id)
            if queues.is_empty(chet_id):
                callsmusic.stop(chet_id)
                await cb.message.edit("- No More Playlist..\n- Leaving VC!")
            else:
                await callsmusic.set_stream(
                    chet_id, 
                    queues.get(chet_id)["file"],
                )
                await cb.answer.reply_text("✅ <b>𝐒𝐤𝐢𝐩𝐩𝐞𝐝</b>")
                await cb.message.edit((m_chat, qeue), reply_markup=r_ply(the_data))
                await cb.message.reply_text(
                    f"- ➡️  𝐒𝐨𝐧𝐠 𝐇𝐚𝐬 𝐁𝐞𝐞𝐧 𝐒𝐤𝐢𝐩𝐩𝐞𝐝 "
                )

    else:
        if chet_id in callsmusic.active_chats:
            try:
                queues.clear(chet_id)
            except QueueEmpty:
                pass

            await callsmusic.stop(chet_id)
            await cb.message.edit("Successfully Left the Chat!")
        else:
            await cb.answer("Chat is not connected!", show_alert=True)
            
     
@Client.on_message(filters.command("play") & filters.group & ~filters.edited)
async def ytplay(_, message: Message):
    global que
    if message.chat.id in DISABLED_GROUPS:
        return
    lel = await message.reply("🔎 **𝐒𝐞𝐚𝐫𝐜𝐡𝐢𝐧𝐠....**")
    administrators = await get_administrators(message.chat)
    chid = message.chat.id

    try:
        user = await USER.get_me()
    except:
        user.first_name = "helper"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                if message.chat.title.startswith("Music: "):
                    await lel.edit(
                        "<b>𝐑𝐞𝐦𝐞𝐦𝐛𝐞𝐫 𝐓𝐨 𝐌𝐚𝐤𝐞 𝐌𝐞 𝐀𝐝𝐦𝐢𝐧</b>",
                    )
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>💡 **𝐀𝐝𝐝 𝐌𝐞 𝐀𝐬 𝐀𝐝𝐦𝐢𝐧 𝐅𝐢𝐫𝐬𝐭 𝐒𝐭𝐮𝐩𝐢𝐝.</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message.chat.id, "𝐇𝐞𝐲 𝐌𝐲 𝐀𝐬𝐬𝐢𝐬𝐭𝐚𝐧𝐭 𝐈𝐬 𝐉𝐨𝐢𝐧𝐞𝐝.. 𝐇𝐮𝐫𝐫𝐞𝐲 🐬🤞"
                    )
                    await lel.edit(
                        "✅ **𝐔𝐬𝐞𝐫𝐛𝐨𝐭 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐉𝐨𝐢𝐧𝐞𝐝**",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>🛑 𝐅𝐥𝐨𝐨𝐝 𝐄𝐫𝐫𝐨𝐫 🛑</b> \n\𝐇𝐞𝐲 {user.first_name},𝐀𝐬𝐬𝐢𝐬𝐭𝐚𝐧𝐭 𝐂𝐨𝐮𝐥𝐝𝐧'𝐭 𝐉𝐨𝐢𝐧 𝐘𝐨𝐮𝐫 𝐆𝐫𝐨𝐮𝐩. 𝐌𝐚𝐲 𝐁𝐞 𝐈𝐭𝐬 𝐁𝐚𝐧𝐧𝐞𝐝 𝐀𝐧𝐝 𝐀𝐧𝐲 𝐎𝐭𝐡𝐞𝐫 𝐈𝐬𝐬𝐮𝐞!</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i> {user.first_name} 𝐔𝐬𝐞𝐫𝐛𝐨𝐭 𝐈𝐬 𝐍𝐨𝐭 𝐈𝐧 𝐂𝐡𝐚𝐭, 𝐓𝐲𝐩𝐞 𝐓𝐡𝐞  /play 𝐂𝐨𝐦𝐦𝐚𝐧𝐝 𝐅𝐢𝐫𝐬𝐭 𝐓𝐨 𝐀𝐝𝐝 𝐀𝐬𝐬𝐢𝐬𝐭𝐚𝐧𝐭 𝐎𝐫 𝐀𝐝𝐝  @{ASSISTANT_NAME} 𝐌𝐚𝐧𝐮𝐚𝐥𝐥𝐲</i>"
        )
        return
    await lel.edit("🔎 𝐏𝐫𝐨𝐜𝐞𝐬𝐬𝐢𝐧𝐠..𝐇𝐨𝐥𝐝 𝐎𝐧")
    message.from_user.id
    message.from_user.first_name

    query = ""
    for i in message.command[1:]:
        query += " " + str(i)
    print(query)
    await lel.edit("🎵 𝐅𝐢𝐧𝐝𝐢𝐧𝐠 𝐘𝐨𝐮𝐫 𝐒𝐨𝐧𝐠")
    ydl_opts = {"format": "bestaudio[ext=m4a]"}
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        url = f"https://youtube.com{results[0]['url_suffix']}"
        # print(results)
        title = results[0]["title"][:40]
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f"thumb{title}.jpg"
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
        duration = results[0]["duration"]
        results[0]["url_suffix"]
        views = results[0]["views"]

    except Exception as e:
        await lel.edit("🤔 𝐖𝐡𝐢𝐜𝐡 𝐒𝐨𝐧𝐠 𝐔 𝐖𝐚𝐧𝐧𝐚 𝐏𝐥𝐚𝐲..")
        print(str(e))
        return
    try:
        secmul, dur, dur_arr = 1, 0, duration.split(":")
        for i in range(len(dur_arr) - 1, -1, -1):
            dur += int(dur_arr[i]) * secmul
            secmul *= 60
        if (dur / 60) > DURATION_LIMIT:
            await lel.edit(
                f"❌ 𝐒𝐨𝐧𝐠 𝐋𝐨𝐧𝐠𝐞𝐫 𝐓𝐡𝐚𝐧 {DURATION_LIMIT} 𝐌𝐢𝐧𝐮𝐭𝐞𝐬 "
            )
            return
    except:
        pass
    dlurl = url
    dlurl = dlurl.replace("youtube", "youtubepp")
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🎬 𝐘𝐨𝐮𝐭𝐮𝐛𝐞",
                    url=f"{url}"
                ),
                InlineKeyboardButton(
                     text="𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝 📥",
                     url=f"{dlurl}"),
            ],
        ]
    )
    requested_by = message.from_user.first_name
    await generate_cover(requested_by, title, views, duration, thumbnail)
    file = await convert(youtube.download(url))
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.active_chats:
        position = await queues.put(chat_id, file=file)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await message.reply_photo(
            photo="final.png",
            caption=f"☑️ **𝐒𝐨𝐧𝐠 𝐀𝐝𝐝𝐞𝐝 𝐀𝐭  »** {position}!",
            reply_markup=keyboard,
        )
        os.remove("final.png")
        return await lel.delete()
    else:
        chat_id = get_chat_id(message.chat)
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            await callsmusic.set_stream(chat_id, file)
        except:
            message.reply("😕 **𝐒𝐭𝐮𝐩𝐢𝐝...𝐓𝐮𝐫𝐧 𝐎𝐧 𝐕𝐨𝐢𝐜𝐞 𝐂𝐡𝐚𝐭 𝐅𝐢𝐫𝐬𝐭 ")
            return
        await message.reply_photo(
            photo="final.png",
            reply_markup=keyboard,
            caption="**🎵 𝐒𝐨𝐧𝐠:** {}\n**🕒 𝐃𝐮𝐫𝐚𝐭𝐢𝐨𝐧:** {} 𝐦𝐢𝐧\n**👤 𝐀𝐝𝐝𝐞𝐝 𝐁𝐲:** {}\n\n**▶️ 𝐍𝐨𝐰 𝐏𝐥𝐚𝐲𝐢𝐧𝐠 𝐀𝐭 `{}`...**".format(
                title,duration,message.from_user.mention(),message.chat.title
            ),
        )
        os.remove("final.png")
        return await lel.delete()


@Client.on_message(filters.command("zplay") & filters.group & ~filters.edited)
async def jiosaavn(client: Client, message_: Message):
    global que
    if message_.chat.id in DISABLED_GROUPS:
        return
    lel = await message_.reply("🔎𝐏𝐫𝐨𝐜𝐞𝐬𝐬𝐢𝐧𝐠...𝐇𝐨𝐥𝐝 𝐎𝐧")
    administrators = await get_administrators(message_.chat)
    chid = message_.chat.id
    try:
        user = await USER.get_me()
    except:
        user.first_name = "AloneMusic"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await client.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message_.from_user.id:
                if message_.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        "<b>𝐑𝐞𝐦𝐞𝐦𝐛𝐞𝐫 𝐓𝐨 𝐀𝐝𝐝 𝐀𝐬𝐬𝐢𝐬𝐭𝐚𝐧𝐭.</b>",
                    )
                try:
                    invitelink = await client.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>𝐀𝐝𝐝 𝐌𝐞 𝐀𝐬 𝐀𝐝𝐦𝐢𝐧 𝐅𝐢𝐫𝐬𝐭 𝐒𝐭𝐮𝐩𝐢𝐝</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await USER.send_message(
                        message_.chat.id, "𝐇𝐞𝐥𝐩𝐞𝐫 𝐉𝐨𝐢𝐧𝐞𝐝 𝐅𝐨𝐫 𝐏𝐥𝐚𝐲 𝐒𝐨𝐧𝐠𝐬"
                    )
                    await lel.edit(
                        "<b>𝐀𝐬𝐬𝐢𝐬𝐭𝐚𝐧𝐭 𝐉𝐨𝐢𝐧𝐞𝐝 𝐇𝐞𝐫𝐞</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>🛑 𝐅𝐥𝐨𝐨𝐝 𝐄𝐫𝐫𝐨𝐫 🛑</b> \n\𝐇𝐞𝐲 {user.first_name},𝐀𝐬𝐬𝐢𝐬𝐭𝐚𝐧𝐭 𝐂𝐨𝐮𝐥𝐝𝐧'𝐭 𝐉𝐨𝐢𝐧 𝐘𝐨𝐮𝐫 𝐆𝐫𝐨𝐮𝐩. 𝐌𝐚𝐲 𝐁𝐞 𝐈𝐭𝐬 𝐁𝐚𝐧𝐧𝐞𝐝 𝐀𝐧𝐝 𝐀𝐧𝐲 𝐎𝐭𝐡𝐞𝐫 𝐈𝐬𝐬𝐮𝐞!",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            "<i> helper Userbot not in this chat, Ask admin to send /play command for first time or add assistant manually</i>"
        )
        return
    requested_by = message_.from_user.first_name
    chat_id = message_.chat.id
    text = message_.text.split(" ", 1)
    query = text[1]
    res = lel
    await res.edit(f"🔍𝐏𝐫𝐨𝐜𝐞𝐬𝐬𝐢𝐧𝐠...𝐇𝐨𝐥𝐝 𝐎𝐧")
    try:
        songs = await arq.saavn(query)
        if not songs.ok:
            await message_.reply_text(songs.result)
            return
        sname = songs.result[0].song
        slink = songs.result[0].media_url
        ssingers = songs.result[0].singers
        sthumb = songs.result[0].image
        sduration = int(songs.result[0].duration)
    except Exception as e:
        await res.edit("𝐅𝐨𝐮𝐧𝐝 𝐍𝐨𝐭𝐡𝐢𝐧𝐠.")
        print(str(e))
        return
    try:
        duuration = round(sduration / 60)
        if duuration > DURATION_LIMIT:
            await cb.message.edit(
                f"𝐒𝐨𝐧𝐠 𝐋𝐨𝐧𝐠𝐞𝐫 𝐓𝐡𝐚𝐧 {DURATION_LIMIT} 𝐌𝐢𝐧𝐮𝐭𝐞𝐬"
            )
            return
    except:
        pass
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="🎬 𝐘𝐨𝐮𝐭𝐮𝐛𝐞", 
                    url=f"{url}"
                ),
                InlineKeyboardButton(
                     text="𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝 📥", 
                     url=f"{dlurl}"),
            ],
        ]
    )
    file = await convert(wget.download(slink))
    chat_id = get_chat_id(message_.chat)
    if chat_id in callsmusic.active_chats:
        position = await queues.put(chat_id, file=file)
        qeue = que.get(chat_id)
        s_name = sname
        r_by = message_.from_user
        loc = file
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await res.delete()
        m = await client.send_photo(
            chat_id=message_.chat.id,
            reply_markup=keyboard,
            photo="final.png",
            caption=f"☑️ **𝐒𝐨??𝐠 𝐀𝐝𝐝𝐞𝐝 𝐓𝐨 𝐐𝐮𝐞𝐮𝐞 »**  {position}",
        )

    else:
        await res.edit_text(f"{bn}=▶️ 𝐏𝐥𝐚𝐲𝐢𝐧𝐠.....")
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = sname
        r_by = message_.from_user
        loc = file
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            await callsmusic.set_stream(chat_id, file)
        except:
            res.edit("😕 **𝐒𝐭𝐮𝐩𝐢𝐝...𝐓𝐮𝐫𝐧 𝐎𝐧 𝐕𝐨𝐢𝐜𝐞 𝐂𝐡𝐚𝐭 𝐅𝐢𝐫𝐬𝐭")
            return
    await res.edit("Generating Thumbnail.")
    await generate_cover(requested_by, sname, ssingers, sduration, sthumb)
    await res.delete()
    m = await client.send_photo(
        chat_id=message_.chat.id,
        reply_markup=keyboard,
        photo="final.png",
        caption=f" {sname} Via saavn",
    )
    os.remove("final.png")