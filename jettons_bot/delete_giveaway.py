from os import getenv
from asyncio import run
from dotenv import load_dotenv
import argparse
from aiogram.exceptions import TelegramForbiddenError

from aiogram import Bot

from jettons_bot.crud import *

load_dotenv()

bot = Bot(token=getenv("TEST_BOT_TOKEN"))

gives_db_path = f"jettons_bot/databases/giveaways.db"
posts_db_path = f"jettons_bot/databases/posts.db"

async def delete_giveaway(giveaway_id: int):
    giveaway_data = await read(
        db_path=gives_db_path, 
        table="giveaways", 
        columns="title, user_id, channel_post_id, channel_id, status", 
        conditions=f"id={giveaway_id}")[0]
    
    channel_id = int(giveaway_data[3])
    post_id = int(giveaway_data[2])
    user_id = int(giveaway_data[1])
    title = giveaway_data[0]
    status = giveaway_data[4]
    if status == "active":
        try:
            is_deleted = await bot.delete_message(
                chat_id=channel_id,
                message_id=post_id
            )
        except TelegramForbiddenError:
            text = f'''
                Раздача \"{title}\" завершена, но не удается удалить пост в канале.
                Возможно, бот утратил права админа. Удалите пост вручную'''
            await bot.send_message(user_id, text)
            
            return

        if not is_deleted:
            text = f'''
                Раздача \"{title}\" завершена, но не удается удалить пост в канале.
                Возможно, бот утратил права админа. Удалите пост вручную'''
            await bot.send_message(user_id, text)
            
            return
        
        text = f'''Раздача \"{title}\" завершена, пост удален из канала'''
        await bot.send_message(user_id, text)

        await update(
            db_path=gives_db_path,
            table="giveaways",
            columns={
                "status":"completed",
            },
            conditions=f"id={giveaway_id}"
        )
    else:
        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-id')
    args = parser.parse_args()
    giveaway_id = int(args.id)

    run(delete_giveaway(giveaway_id))