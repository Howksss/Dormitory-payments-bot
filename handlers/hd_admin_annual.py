from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import Bot
from database.queries.orm import Users, PnDs, Bills
from keyboards.kb_admin import admin_use, BillsAction, AdminActions, ProBillsAction, AnnualPayActions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database.config import settings
import datetime
from typing import Optional, List

router = Router()
bot = Bot(settings.TOKEN)
db = PnDs() 
usr_db = Users()
bills_db = Bills()

class AnnualPay(StatesGroup):
    pay_amount = State()
    current_level = State()


class AnnualPayNavigator():

    @staticmethod
    async def get_annual_keyboard(level: int):
        builder = InlineKeyboardBuilder()
        match level:
            case 1:
                builder.row(
                    InlineKeyboardButton(
                        text="Назад", 
                        callback_data=AnnualPayActions(
                            action="exit",
                            level=level,  
                        ).pack()
                    ))
            case 2:
                builder.row(
                        InlineKeyboardButton(
                        text="Подтвердить", 
                        callback_data=AnnualPayActions(
                            action="confirm",
                            level=level,  
                        ).pack()
                    ),
                    InlineKeyboardButton(
                        text="Назад", 
                        callback_data=AnnualPayActions(
                            action="back",
                            level=level,  
                        ).pack()
                    ))
        return builder.as_markup()




    @staticmethod
    async def show_admin_panel(chat_id: int):
        await bot.send_photo(
            chat_id=chat_id,
            photo=await db.get_pic("admin_panel_0"),
            caption=await db.get_desc("admin_panel_0"),
            parse_mode='HTML',
            reply_markup=await admin_use(0)
        )

@router.callback_query(AnnualPayActions.filter())
async def handle_annual_pay(callback: CallbackQuery, callback_data: AdminActions, state: FSMContext):
    chat_id = callback.from_user.id
    state_data = await state.get_data()
    if callback_data.action == "exit":
        await callback.message.delete()
        await state.clear()
        await AnnualPayNavigator.show_admin_panel(chat_id)
        return
    elif callback_data.action == "back":
        await callback.message.delete()
        await state.clear()
        await state.set_state(AnnualPay.pay_amount)  
        await bot.send_message(chat_id, text=await db.get_desc("annual_pay_1"), parse_mode='HTML', reply_markup=await AnnualPayNavigator.get_annual_keyboard(1))
    elif callback_data.action == "confirm":
        await callback.message.delete()
        await state.clear()
        await bot.send_message(chat_id=chat_id, text=await usr_db.annual_pay(state_data["pay_amount"]), parse_mode='HTML')
        await AnnualPayNavigator.show_admin_panel(chat_id)

@router.callback_query(AdminActions.filter(F.action == "annual_pay"))
async def start_annual_pay(callback: CallbackQuery, callback_data: AdminActions, state: FSMContext):
    chat_id = callback.from_user.id
    await state.set_state(AnnualPay.pay_amount)
    await callback.message.delete()
    await bot.send_message(chat_id, text=await db.get_desc("annual_pay_1"), parse_mode='HTML', reply_markup=await AnnualPayNavigator.get_annual_keyboard(1))

    
@router.message(AnnualPay.pay_amount, F.text)
async def recieve_annual_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму (число)")
        return
    await state.update_data(pay_amount=amount)
    await message.answer(f"Введенная сумма: {amount}, подтвердите корректность", parse_mode = 'HTML', reply_markup=await AnnualPayNavigator.get_annual_keyboard(2))