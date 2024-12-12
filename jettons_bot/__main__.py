import asyncio
from jettons_bot.handlers import (
    channels,
    common,
    posts,
    giveaways)

from jettons_bot.create_databases import create_tables
from aiogram import Bot, Dispatcher
from os import getenv
from dotenv import load_dotenv

async def main():
    load_dotenv()
    create_tables()

    bot = Bot(token=getenv("TEST_BOT_TOKEN"))
    dp = Dispatcher()

    dp.include_router(channels.router)
    dp.include_router(giveaways.router)
    dp.include_router(common.router)
    dp.include_router(posts.router)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())