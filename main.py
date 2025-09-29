import asyncio
from database.config import settings
from aiogram import Bot, Dispatcher
from handlers import hd_admin_bills, hd_main, hd_admin_annual, hd_admin_export, hd_admin_manage_users

async def main():
    bot = Bot(settings.TOKEN)
    dp = Dispatcher()
    dp.include_routers(hd_main.router, hd_admin_bills.router, hd_admin_annual.router, hd_admin_export.router, hd_admin_manage_users.router)    #Добавляем все роутеры
    dp["bot"] = bot  
    await bot.delete_webhook(drop_pending_updates=True)   #Пропускаем все сообщения, отправленные до запуска бота
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())