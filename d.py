import asyncio
from datetime import datetime, timedelta
import os

from pyrogram.enums import parse_mode
from pyrogram import Client, filters
from pyrogram.types import Message, User
from dotenv import load_dotenv

load_dotenv()

api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')
session = os.getenv('session')

if api_id is None or api_hash is None or session is None:
    print('api参数错误和session参数错误,请修改.env文件中的参数')
    exit()

data = []
with open('id', 'r', encoding='utf-8') as file:
    lines = file.readlines()
    for line in lines:
        tg_id = line.replace('\n', '')
        data.append(tg_id)

app = Client(session, api_id=api_id, api_hash=api_hash)
count_deleted = 0
running = False
count_running = 0

groups = {-1001464555457, -1001438560068, -1001353656864, -1001416676398, -1001549263396, -1001518421010,
          -1001518421010, -1001440784384}


async def ban_all(group_id):
    global count_deleted
    for user_id in data:
        try:
            await app.ban_chat_member(chat_id=group_id, user_id=user_id,
                                      until_date=datetime.now() + timedelta(seconds=35))
            count_deleted += 1
        except Exception as e:
            print(e)
            continue

    await app.send_message(chat_id=group_id,
                           text=f'已清理 <code>{count_deleted}</code> 用户',
                           parse_mode=parse_mode.ParseMode.HTML)

    count_deleted = 0


@app.on_message(filters.command('run'))
async def clean(client: Client, message: Message):
    global count_deleted
    global count_running
    global groups
    for group in groups:
        print(f'正在检查第 {count_running} 个群')
        await app.send_message(chat_id=group,
                               text=f'正在检查第 {count_running} 个群',
                               parse_mode=parse_mode.ParseMode.HTML)
        count_running += 1
        await ban_all(group)


app.run()
