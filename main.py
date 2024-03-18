import asyncio

from aiogram import Bot, Dispatcher


from config_data.config import load_config
from routers import router as main_router

config = load_config()


async def main() -> None:
    BOT_TOKEN: str = config.tg_bot.token
    bot: "Bot" = Bot(token=BOT_TOKEN)

    dp: "Dispatcher" = Dispatcher()

    dp.include_router(main_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


asyncio.run(main())
