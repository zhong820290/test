import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import Message, ChatAdminWithInviteLinks
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

running = False
count_running = 0


@app.on_message(filters.command('print'))
async def print_all(client: Client, message: Message):
    global running
    global count_running

    await message.delete()
    if running:
        res = await message.reply("错误：已有正在运行的任务")
        await asyncio.sleep(5)  # 等待5秒
        await res.delete()
        return
    if message.from_user is not None:
        try:
            chat_member = await client.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)

            p = chat_member.status.value

            if p == 'owner' or p == 'administrator':
                pass
            else:
                await message.reply("错误：已有正在运行的任务")
                return

        except Exception as e:
            print(e)
            res = await message.reply("错误：请在群组中发送")
            await asyncio.sleep(5)  # 等待5秒
            await res.delete()
            return
    try:
        group_id=message.chat.id
        admins_links = await app.get_chat_admins_with_invite_links(chat_id=group_id)
        for admins_link in admins_links:
            # admins_link: ChatAdminWithInviteLinks

            async for link_revoked in app.get_chat_admin_invite_links(chat_id=group_id, admin_id=admins_link.admin.id, revoked=True):
                count_running += 1
                print(str(link_revoked.invite_link) + "\n")
            async for link in app.get_chat_admin_invite_links(chat_id=group_id, admin_id=admins_link.admin.id):
                count_running += 1
                print(str(link.invite_link) + "\n")

        print(f'共有 {count_running} 邀请链接')
        await message.reply(f'共有 {count_running} 邀请链接')
        count_running = 0
        running = False
    except Exception as e:
        print(e)
        count_running = 0
        running = False


app.run()
