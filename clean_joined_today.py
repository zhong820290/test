import asyncio
import json
import time
from datetime import datetime, timedelta
import os
import pytz
from pyrogram.enums import parse_mode
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv

load_dotenv()

api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')
session = os.getenv('session')

groups_data = os.getenv('groups')
groups = set()

try:
    groups = set(json.loads(groups_data))
except Exception as e:
    print(e)
    exit("配置中的群组格式错误,请检查后重新运行!")

if api_id is None or api_hash is None or session is None:
    exit('api参数错误和session参数错误,请修改.env文件中的参数')

proxy = {
    "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
    "hostname": "127.0.0.1",
    "port": 7890
}
# app = Client(session, api_id=api_id, api_hash=api_hash, proxy=proxy)
app = Client(session, api_id=api_id, api_hash=api_hash)
shanghai_tz = pytz.timezone('Asia/Shanghai')

ing = False

@app.on_message(filters.command('cjt'))
async def clean_joined_today(client: Client, message: Message):
    global ing
    if ing:
        await message.reply("已运行")
        return
    else:
        ing = True
        await message.reply("开始清理...")
    now = datetime.now(shanghai_tz)
    count = 0
    try:
        async for user in app.get_chat_invite_link_joiners(chat_id=message.chat.id, invite_link=message.command[1]):
            user_join = user.date.astimezone(shanghai_tz)
            if user_join.date() == now.date():
                await app.ban_chat_member(chat_id=message.chat.id,user_id=user.user.id,until_date=datetime.now(shanghai_tz) + timedelta(seconds=35))
                count += 1
                time.sleep(1)

        await message.reply(f"已清理{count}")
    except Exception as e:
        await message.reply(f"{e}")
        await message.reply(f"已清理{count}")
        ing = False


app.run()
