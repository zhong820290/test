import asyncio
import json
from datetime import datetime, timedelta
import os
from pyrogram.enums import parse_mode
from pyrogram import Client, filters
from pyrogram.types import Message
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
app = Client(session, api_id=api_id, api_hash=api_hash)

count_deleted = 0
running = False
count_running = 0

groups = {-1001464555457, -1001438560068, -1001353656864, -1001416676398, -1001549263396, -1001440784384,
          -1001262151163, -1001540550248, -1001518421010}

deleted_user = set()

clean_id_path = 'clean_id'
if not os.path.exists(clean_id_path):
    os.makedirs(clean_id_path)


async def ban_all(group_id):
    global count_deleted
    for user_id in deleted_user:
        try:
            member = await app.get_chat_member(chat_id=group_id, user_id=user_id)
            if member.user.is_deleted:
                await app.ban_chat_member(chat_id=group_id, user_id=user_id,
                                          until_date=datetime.now() + timedelta(seconds=35))
                count_deleted += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            print(e)
            continue

    await app.send_message(chat_id=group_id,
                           text=f'已清理 <code>{count_deleted}</code> 用户',
                           parse_mode=parse_mode.ParseMode.HTML)

    count_deleted = 0


def save_deleted_user(do_time):
    global deleted_user
    global clean_id_path
    with open(f'{clean_id_path}/deleted_user_{do_time}.txt', 'w', encoding='utf-8') as f:
        json.dump({"deleted_user": list(deleted_user)}, f)


@app.on_message(filters.command('clean'))
async def clean(client: Client, message: Message):
    global count_deleted
    global running
    global count_running
    global deleted_user
    global groups
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
    else:
        running = True

    current_time = datetime.now().strftime("%Y年%m月%d日_%H时%M分%S秒")
    group_id = message.chat.id
    await client.send_message(chat_id=group_id, text=f'正在清理...',
                              parse_mode=parse_mode.ParseMode.HTML)

    try:

        async for link_revoked in app.get_chat_admin_invite_links(chat_id=group_id, admin_id='me', revoked=True):
            try:
                joiners_revoked = app.get_chat_invite_link_joiners(chat_id=group_id, invite_link=link_revoked.invite_link)
                async for joiner_revoked in joiners_revoked:
                    count_running += 1
                    print(f"正在检查第 {count_running} 用户\n")
                    if joiner_revoked.user.is_deleted:

                        try:
                            await app.ban_chat_member(chat_id=group_id, user_id=joiner_revoked.user.id,
                                                      until_date=datetime.now() + timedelta(seconds=35))
                            deleted_user.add(joiner_revoked.user.id)
                            save_deleted_user(current_time)
                            # await app.unban_chat_member(chat_id=group_id, user_id=joiner_revoked.user.id)
                            count_deleted += 1
                        except Exception as e:
                            print(e)
                            continue
            except Exception as e:
                print(e)
                continue
        async for link in app.get_chat_admin_invite_links(chat_id=group_id, admin_id='me'):
            try:
                joiners = app.get_chat_invite_link_joiners(chat_id=group_id, invite_link=link.invite_link)
                async for joiner in joiners:
                    count_running += 1
                    print(f"正在检查第 {count_running} 用户\n")
                    if joiner.user.is_deleted:
                        try:
                            await app.ban_chat_member(chat_id=group_id, user_id=joiner.user.id,
                                                      until_date=datetime.now() + timedelta(seconds=35))
                            deleted_user.add(joiner.user.id)
                            save_deleted_user(current_time)
                            # await app.unban_chat_member(chat_id=group_id, user_id=joiner.user.id)
                            count_deleted += 1
                        except Exception as e:
                            print(e)
                            continue
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

    await client.send_message(chat_id=group_id, text=f'开始交叉清理...')

    if count_deleted == 0:
        await client.send_message(chat_id=group_id, text=f'无需交叉清理')
        deleted_user.clear()
        running = False
        count_deleted = 0
        count_running = 0
        return

    count_deleted = 0
    count_running = 1
    for group in groups:
        print(f'正在检查第 {count_running} 个群')
        await app.send_message(chat_id=group,
                               text=f'正在检查第 {count_running} 个群',
                               parse_mode=parse_mode.ParseMode.HTML)
        count_running += 1
        await ban_all(group)
    deleted_user.clear()
    running = False
    count_deleted = 0
    count_running = 0


count_link = 0
count_admin = 0

@app.on_message(filters.command('owner_clean'))
async def owner_clean(client: Client, message: Message):
    global count_deleted
    global running
    global count_running
    global deleted_user
    global groups
    global count_link
    global count_admin
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
                running = True
            else:
                await message.reply("错误：对不起您没有权限")
                return

        except Exception as e:
            print(e)
            res = await message.reply("错误：请在群组中发送")
            await asyncio.sleep(5)  # 等待5秒
            await res.delete()
            return
    else:
        running = True

    group_id = message.chat.id
    current_time = datetime.now().strftime("%Y年%m月%d日_%H时%M分%S秒")
    await client.send_message(chat_id=group_id, text=f'正在全面清理...',
                              parse_mode=parse_mode.ParseMode.HTML)
    try:

        admins = await app.get_chat_admins_with_invite_links(chat_id=group_id)
        for admin in admins:
            print(f"正在检查第 {count_admin} 个管理的链接\n")
            async for link_revoked in app.get_chat_admin_invite_links(chat_id=group_id, admin_id=admin.admin.id,
                                                                      revoked=True):

                try:
                    joiners_revoked = app.get_chat_invite_link_joiners(chat_id=group_id,
                                                                       invite_link=link_revoked.invite_link)
                    count_link += 1
                    print(f"正在检查第 {count_link} 个链接\n")
                    async for joiner_revoked in joiners_revoked:
                        count_running += 1
                        print(f"正在检查第 {count_running} 用户\n")
                        if joiner_revoked.user.is_deleted:

                            try:
                                await app.ban_chat_member(chat_id=group_id, user_id=joiner_revoked.user.id,
                                                          until_date=datetime.now() + timedelta(seconds=35))
                                deleted_user.add(joiner_revoked.user.id)
                                save_deleted_user(current_time)
                                count_deleted += 1
                            except Exception as e:
                                print(e)
                                continue
                except Exception as e:
                    print(e)
                    continue

            async for link in app.get_chat_admin_invite_links(chat_id=group_id, admin_id=admin.admin.id):

                try:
                    joiners = app.get_chat_invite_link_joiners(chat_id=group_id, invite_link=link.invite_link)
                    count_link += 1
                    print(f"正在检查第 {count_link} 个链接\n")
                    async for joiner in joiners:
                        count_running += 1
                        print(f"正在检查第 {count_running} 用户\n")
                        if joiner.user.is_deleted:
                            try:
                                await app.ban_chat_member(chat_id=group_id, user_id=joiner.user.id,
                                                          until_date=datetime.now() + timedelta(seconds=35))
                                deleted_user.add(joiner.user.id)
                                save_deleted_user(current_time)
                                count_deleted += 1
                            except Exception as e:
                                print(e)
                                continue
                except Exception as e:
                    print(e)
                    continue

            count_admin += 1
    except Exception as e:
        print(e)
        running = False
        count_deleted = 0
        count_running = 0
        count_link = 0
        count_admin = 0
        await client.send_message(chat_id=group_id, text=f'错误,无法获取邀请链接.')
        return

    await client.send_message(chat_id=group_id,
                              text=f'总共检查 <code>{count_admin}</code> 个管理 <code>{count_link}</code> 个链接 <code>{count_running}</code> 用户,已清理 <code>{count_deleted}</code> 用户',
                              parse_mode=parse_mode.ParseMode.HTML)

    await client.send_message(chat_id=group_id, text=f'开始交叉清理...')

    if count_deleted == 0:
        await client.send_message(chat_id=group_id, text=f'无需交叉清理')
        deleted_user.clear()
        running = False
        count_deleted = 0
        count_running = 0
        count_link = 0
        count_admin = 0
        return
    else:
        count_deleted = 0
        count_running = 1
        for group in groups:
            print(f'正在检查第 {count_running} 个群')
            await app.send_message(chat_id=group,
                                   text=f'正在检查第 {count_running} 个群',
                                   parse_mode=parse_mode.ParseMode.HTML)
            count_running += 1
            await ban_all(group)
        deleted_user.clear()
        running = False
        count_deleted = 0
        count_running = 0
        count_link = 0
        count_admin = 0

@app.on_message(filters.command('clean_all'))
async def clean_all(client: Client, message: Message):
    global count_deleted
    global running
    global count_running
    global deleted_user
    global groups
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
    else:
        running = True


    for group_id in groups:
        current_time = datetime.now().strftime("%Y年%m月%d日_%H时%M分%S秒")
        await client.send_message(chat_id=group_id, text=f'正在全自动清理...',
                                  parse_mode=parse_mode.ParseMode.HTML)

        try:

            admins_links = await app.get_chat_admins_with_invite_links(chat_id=group_id)
            for admins_link in admins_links:
                print(admins_link)

            async for link_revoked in app.get_chat_admin_invite_links(chat_id=group_id, admin_id='me', revoked=True):
                try:
                    joiners_revoked = app.get_chat_invite_link_joiners(chat_id=group_id,
                                                                       invite_link=link_revoked.invite_link)
                    async for joiner_revoked in joiners_revoked:
                        count_running += 1
                        print(f"正在检查第 {count_running} 用户\n")
                        if joiner_revoked.user.is_deleted:

                            try:
                                await app.ban_chat_member(chat_id=group_id, user_id=joiner_revoked.user.id,
                                                          until_date=datetime.now() + timedelta(seconds=35))
                                deleted_user.add(joiner_revoked.user.id)
                                save_deleted_user(current_time)
                                # await app.unban_chat_member(chat_id=group_id, user_id=joiner_revoked.user.id)
                                count_deleted += 1
                            except Exception as e:
                                print(e)
                                continue
                except Exception as e:
                    print(e)
                    continue
            async for link in app.get_chat_admin_invite_links(chat_id=group_id, admin_id='me'):
                try:
                    joiners = app.get_chat_invite_link_joiners(chat_id=group_id, invite_link=link.invite_link)
                    async for joiner in joiners:
                        count_running += 1
                        print(f"正在检查第 {count_running} 用户\n")
                        if joiner.user.is_deleted:
                            try:
                                await app.ban_chat_member(chat_id=group_id, user_id=joiner.user.id,
                                                          until_date=datetime.now() + timedelta(seconds=35))
                                deleted_user.add(joiner.user.id)
                                save_deleted_user(current_time)
                                # await app.unban_chat_member(chat_id=group_id, user_id=joiner.user.id)
                                count_deleted += 1
                            except Exception as e:
                                print(e)
                                continue
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
            continue

        await client.send_message(chat_id=group_id,
                                  text=f'总共检查 <code>{count_running}</code> 用户,已清理 <code>{count_deleted}</code> 用户',
                                  parse_mode=parse_mode.ParseMode.HTML)

        await client.send_message(chat_id=group_id, text=f'开始全自动交叉清理...')

        if count_deleted == 0:
            await client.send_message(chat_id=group_id, text=f'无需全自动交叉清理。')
            deleted_user.clear()
            running = False
            count_deleted = 0
            count_running = 0
            continue

        count_deleted = 0
        count_running = 1
        for group in groups:
            if group == group_id:
                continue
            print(f'正在检查第 {count_running} 个群')
            await app.send_message(chat_id=group,
                                   text=f'正在检查第 {count_running} 个群',
                                   parse_mode=parse_mode.ParseMode.HTML)
            count_running += 1
            await ban_all(group)
        deleted_user.clear()
        running = False
        count_deleted = 0
        count_running = 0


app.run()
