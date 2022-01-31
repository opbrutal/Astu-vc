from asyncio.queues import QueueEmpty
from config import BOT_USERNAME
from config import que
from pyrogram import Client, filters
from pyrogram.types import Message
import sira
import DeCalls
from cache.admins import set
from helpers.decorators import authorized_users_only, errors
from helpers.channelmusic import get_chat_id
from helpers.filters import command, other_filters
from Client import callsmusic
from pytgcalls.types.input_stream import InputAudioStream
from pytgcalls.types.input_stream import InputStream


@Client.on_message(command(["pause", "jeda"]) & other_filters)
@errors
@authorized_users_only
async def pause(_, message: Message):
    await callsmusic.pytgcalls.pause_stream(message.chat.id)
    await message.reply_text("▶️ 𝙋𝙖𝙪𝙨𝙚𝙙"
    )


@Client.on_message(command(["resume", "lanjut"]) & other_filters)
@errors
@authorized_users_only
async def resume(_, message: Message):
    await callsmusic.pytgcalls.resume_stream(message.chat.id)
    await message.reply_text("⏸ 𝙍𝙚𝙨𝙪𝙢𝙚𝙙 "
    )


@Client.on_message(command(["end", "stop"]) & other_filters)
@errors
@authorized_users_only
async def stop(_, message: Message):
    try:
        callsmusic.queues.clear(message.chat.id)
    except QueueEmpty:
        pass

    await callsmusic.pytgcalls.leave_group_call(message.chat.id)
    await message.reply_text("❌ 𝙎𝙩𝙧𝙚𝙖𝙢𝙞𝙣𝙜 𝙎𝙩𝙤𝙥𝙥𝙚𝙙."
    )

@Client.on_message(command(["skip", "second", "next", f"next@{BOT_USERNAME}"]) & other_filters)
@errors
@authorized_users_only
async def skip(_, message: Message):
    global que
    chat_id = message.chat.id
    ACTV_CALLS = {}
    for x in callsmusic.pytgcalls.active_calls:
        ACTV_CALLS(int(x.chat_id))
    if int(chat_id) not in ACTV_CALLS:
        await message.reply_text("𝙉𝙤 𝘼𝙣𝙮 𝙎𝙤𝙣𝙜 𝙄𝙨 𝙋𝙡𝙖𝙮𝙞𝙣𝙜 𝙁𝙤𝙧 𝙎𝙠𝙞𝙥...")
    else:
        queues.task_done(chat_id)
        
        if queues.is_empty(chat_id):
            await callsmusic.pytgcalls.leave_group_call(chat_id)
        else:
            await callsmusic.pytgcalls.change_stream(
                chat_id, 
                InputStream(
                    InputAudioStream(
                        callsmusic.queues.get(chat_id)["file"],
                    ),
                ),
            )
                
    qeue = que.get(chat_id)
    if qeue:
        qeue.pop(0)
    if not qeue:
        return
    await message.reply_text(""➡️ 𝙎𝙤𝙣𝙜 𝙃𝙖𝙨 𝘽𝙚𝙚𝙣 𝙎𝙠𝙞𝙥𝙥𝙚𝙙.")




@Client.on_message(filters.command(["reload", "refresh"]))
@errors
@authorized_users_only
async def admincache(client, message: Message):
    set(
        message.chat.id,
        (
            member.user
            for member in await message.chat.get_members(filter="administrators")
        ),
    )

    await message.reply_text("𝙍𝙚𝙡𝙤𝙖𝙙𝙚𝙙🔉"
                              
    )
