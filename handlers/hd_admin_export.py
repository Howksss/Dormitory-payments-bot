from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import Bot
from database.queries.orm import Users, PnDs, Bills
from keyboards.kb_admin import admin_use, BillsAction, AdminActions, ProBillsAction, AnnualPayActions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import FSInputFile
from aiogram.types import InlineKeyboardButton
from database.config import settings
from database.export_db import export_to_excel
import datetime
from typing import Optional, List

router = Router()
bot = Bot(settings.TOKEN)
db = PnDs() 
usr_db = Users()
bills_db = Bills()


class Export():
    @staticmethod
    async def show_admin_panel(chat_id: int):
        await bot.send_photo(
            chat_id=chat_id,
            photo=await db.get_pic("admin_panel_0"),
            caption=await db.get_desc("admin_panel_0"),
            parse_mode='HTML',
            reply_markup=await admin_use(0)
        )


    @staticmethod
    async def send_excel(chat_id:int):
        res = await export_to_excel()
        if res:
            exported_db = FSInputFile("database/exported_users.xlsx")
            await bot.send_document(
                chat_id=chat_id,
                document=exported_db
            )
            return
        else: return False

@router.callback_query(AdminActions.filter(F.action == "export"))
async def start_annual_pay(callback: CallbackQuery, callback_data: AdminActions, state: FSMContext):
    chat_id = callback.from_user.id
    await callback.message.delete()
    if await Export.send_excel(chat_id) == False:
        await bot.send_message(chat_id, text = "Не удалось отправить бд")
    await Export.show_admin_panel(chat_id)