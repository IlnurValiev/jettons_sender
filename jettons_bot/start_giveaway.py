from os import getenv
from asyncio import run
from dotenv import load_dotenv
import argparse
from aiogram.exceptions import TelegramForbiddenError
from crontab import CronTab
from datetime import datetime, timedelta

from aiogram import Bot

from jettons_bot.crud import *
from jettons_bot.buttons_factory import resend_post_button, get_jettons_button

from platform import system

load_dotenv()

bot = Bot(token=getenv("TEST_BOT_TOKEN"))

gives_db_path = f"jettons_bot/databases/giveaways.db"
posts_db_path = f"jettons_bot/databases/posts.db"

current_os = system()

async def start_giveaway(giveaway_id: int):
    giveaway_data = await read(
        db_path=gives_db_path, 
        table="giveaways", 
        columns="title, user_id, post_id, channel_id, status, delete_hours", 
        conditions=f"id={giveaway_id}")[0]
    if giveaway_data:
        status = giveaway_data[-2]
        if status == "scheduled":
            channel_id = int(giveaway_data[3])
            post_id = int(giveaway_data[2])
            user_id = int(giveaway_data[1])
            title = giveaway_data[0]

            bot_chat = await bot.get_me()
            try:
                bot_member = await bot.get_chat_member(channel_id, bot_chat.id)
            except TelegramForbiddenError:
                text = f'''
                        Для раздачи \"{title}\" нет доступа в канал. 
                        Возможно, он был удален из Telegram или бот был забанен в нём.
                        Проверьте наличие канала и бота в админ. панели и попробуйте еще раз'''
                button = await resend_post_button(giveaway_id)
                await bot.send_message(user_id, text, reply_markup=button)

                return
            
            if not bot_member.can_post_messages:
                text = f'''
                        Для раздачи \"{title}\" нет прав публиковать в канал. 
                        Предоставьте права и попробуйте еще раз'''
                button = await resend_post_button(giveaway_id)
                await bot.send_message(user_id, text, reply_markup=button)
                
                return
            
            post_data = await read(
                db_path=posts_db_path,
                table="posts",
                columns="button_text, text, media_id, media_type, has_spoiler",
                conditions=f"post_id={post_id}"
            )[0]

            if not post_data:
                return
            
            button_text = post_data[0]
            text = post_data[1]
            media_id = post_data[2]
            media_type = post_data[3]
            has_spoiler = post_data[4]
            
            button = await get_jettons_button(giveaway_id, button_text, bot=bot)

            if media_type == "photo":
                post = await bot.send_photo(
                    chat_id=channel_id,
                    photo=media_id,
                    caption=text, 
                    parse_mode="MarkdownV2",
                    has_spoiler=has_spoiler,
                    reply_markup=button)
            elif media_type == "video":
                post = await bot.send_video(
                    chat_id=channel_id,
                    video=media_id,
                    caption=text, 
                    parse_mode="MarkdownV2",
                    has_spoiler=has_spoiler,
                    reply_markup=button)
            else:        
                post = await bot.send_message(
                    chat_id=channel_id,
                    text=text, 
                    parse_mode="MarkdownV2", 
                    reply_markup=button)

            await bot.send_message(
                chat_id=user_id,
                text=f"Раздача \"{title}\" запущена!")
            
            await update(
                db_path=gives_db_path,
                table="giveaways",
                columns={
                    "status":"active",
                    "channel_post_id": post.message_id
                },
                conditions=f"id={giveaway_id}"
            )

            delete_hours = int(giveaway_data[-1])

            cron = CronTab(user=True)
            
            if current_os == "Windows":
                command = f"c:/Users/ilnur/ju_bots/ju_bots/venv/Scripts/python.exe jettons_bot/delete_giveaway.py -id {giveaway_id}"
            else:
                command = f"python /root/ju_bots/jettons_bot/jettons_bot/delete_giveaway.py -id {giveaway_id}"

            job = cron.new(command=command)
            
            current_time = datetime.now()
            delta = timedelta(hours=delete_hours)
            mins_delta = timedelta(minutes=2)
            dtime = current_time + delta - mins_delta
            
            job.setall(dtime)

            cron.write()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-id')
    args = parser.parse_args()
    giveaway_id = int(args.id)

    run(start_giveaway(giveaway_id))