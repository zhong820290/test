import asyncio
import json
import time
from datetime import datetime, timedelta
import os

from pyrogram.enums import parse_mode
from pyrogram import Client, filters
from pyrogram.types import Message, User, ChatEventFilter, ChatEvent
from dotenv import load_dotenv

load_dotenv()

api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')
session = os.getenv('session')

if api_id is None or api_hash is None or session is None:
    print('api参数错误和session参数错误,请修改.env文件中的参数')
    exit()

proxy = {
    "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
    "hostname": "127.0.0.1",
    "port": 7890
}
# app = Client(session, api_id=api_id, api_hash=api_hash, proxy=proxy)

app = Client(session, api_id=api_id, api_hash=api_hash)

running = False


@app.on_message(filters.command('ka'))
async def kick_all(client: Client, message: Message):
    global running
    if running:
        res = await message.reply("错误：已有正在运行的任务")
        await asyncio.sleep(5)  # 等待5秒
        await res.delete()
        return
    running = True
    group_id = message.chat.id
    while True:
        try:
            members = app.get_chat_members(chat_id=group_id)
            async for member in members:
                user_id = member.user.id
                await app.ban_chat_member(chat_id=group_id, user_id=user_id,
                                          until_date=datetime.now() + timedelta(seconds=35))
            await asyncio.sleep(0.1)
        except Exception as e:
            print(e)

app.run()
