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

# proxy = {
#     "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
#     "hostname": "127.0.0.1",
#     "port": 7890
# }
app = Client(session, api_id=api_id, api_hash=api_hash)
count_deleted = 0
running = False
count_running = 0


@app.on_message(filters.command('clean'))
async def clean(client: Client, message: Message):
    global count_deleted
    global running
    global count_running
    await message.delete()
    if running:
        res = await message.reply("错误：已有正在运行的任务")
        await asyncio.sleep(5)  # 等待5秒
        await res.delete()
        return

    try:
        chat_member = await client.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)

        p = chat_member.status.value

        if p == 'owner' or p == 'administrator':
            running = True
        else:
            res = await message.reply("错误：您尚未拥有权限")
            await asyncio.sleep(5)  # 等待5秒
            await res.delete()
            return
    except Exception as e:
        print(e)
        res = await message.reply("错误：请在群组中发送")
        await asyncio.sleep(5)  # 等待5秒
        await res.delete()
        return

    group_id = message.chat.id
    await client.send_message(chat_id=group_id, text=f'正在清理...',
                              parse_mode=parse_mode.ParseMode.HTML)

    try:

        async for link_revoked in app.get_chat_admin_invite_links(chat_id=group_id, admin_id='me', revoked=True):
            joiners_revoked = app.get_chat_invite_link_joiners(chat_id=group_id, invite_link=link_revoked.invite_link)
            async for joiner_revoked in joiners_revoked:
                count_running += 1
                print(f"正在检查第 {count_running} 用户\n")
                if joiner_revoked.user.is_deleted:

                    try:

                        await app.ban_chat_member(chat_id=group_id, user_id=joiner_revoked.user.id,
                                                  until_date=datetime.now() + timedelta(seconds=35))
                        # await app.unban_chat_member(chat_id=group_id, user_id=joiner_revoked.user.id)
                        count_deleted += 1
                    except Exception as e:
                        print(e)
                        continue

        async for link in app.get_chat_admin_invite_links(chat_id=group_id, admin_id='me'):
            joiners = app.get_chat_invite_link_joiners(chat_id=group_id, invite_link=link.invite_link)
            async for joiner in joiners:
                count_running += 1
                print(f"正在检查第 {count_running} 用户\n")
                if joiner.user.is_deleted:
                    try:
                        await app.ban_chat_member(chat_id=group_id, user_id=joiner.user.id,
                                                  until_date=datetime.now() + timedelta(seconds=35))
                        # await app.unban_chat_member(chat_id=group_id, user_id=joiner.user.id)
                        count_deleted += 1
                    except Exception as e:
                        print(e)
                        continue
    except Exception as e:
        print(e)
        running = False
        count_deleted = 0
        count_running = 0
        await client.send_message(chat_id=group_id, text=f'错误,无法获取邀请链接.',
                                  parse_mode=parse_mode.ParseMode.HTML)
        return

    await client.send_message(chat_id=group_id,
                              text=f'总共检查 <code>{count_running}</code> 用户,已清理 <code>{count_deleted}</code> 用户',
                              parse_mode=parse_mode.ParseMode.HTML)
    running = False
    count_deleted = 0
    count_running = 0


app.run()
