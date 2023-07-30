import asyncio

from pyrogram.enums import parse_mode
from pyrogram import Client, filters
from pyrogram.types import Message, User

api_id = "填写api_id"
api_hash = "填写api_hash"
bot_token = "填写机器人token"

# proxy = {
#     "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
#     "hostname": "127.0.0.1",
#     "port": 7890
# }

app = Client("test", api_id=api_id, api_hash=api_hash)
bot = Client("test_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
count = 0
running = False


@bot.on_message(filters.command('clean'))
async def clean(client: Client, message: Message):
    global count
    global running
    await message.delete()
    if running:
        res = await message.reply("错误：已有正在运行的任务")
        await asyncio.sleep(5)  # 等待5秒
        await res.delete()
        return

    if len(message.command) < 2:
        running = False
        count = 0
        res = await message.reply("错误：缺少参数。用法：/clean <invite_link>")
        await asyncio.sleep(5)  # 等待5秒
        await res.delete()
        return

    group_id = message.chat.id
    await client.send_message(chat_id=group_id, text=f'正在清理...',
                              parse_mode=parse_mode.ParseMode.HTML)

    invite_link = message.command[1]
    try:
        joiners = app.get_chat_invite_link_joiners(chat_id=group_id, invite_link=invite_link)
        async for joiner in joiners:
            if joiner.user.is_deleted:
                await app.ban_chat_member(chat_id=group_id, user_id=joiner.user.id)
                await app.unban_chat_member(chat_id=group_id, user_id=joiner.user.id)
                count += 1

        await client.send_message(chat_id=group_id, text=f'已清理 <code>{count}</code> 用户',
                                  parse_mode=parse_mode.ParseMode.HTML)
        running = False
        count = 0
    except Exception as e:
        await client.send_message(chat_id=group_id, text=f'运行发生错误,{str(e)}')
        running = False
        count = 0


app.run()
