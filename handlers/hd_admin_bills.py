from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import Bot
from database.queries.orm import Users, PnDs, Bills
from keyboards.kb_admin import admin_use, BillsAction, AdminActions, ProBillsAction
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


class BillListing(StatesGroup):
    current_level = State()  
    bill_size = State()  
    money_message_id = State()
    bills_message_id = State()
    # current_bill_owner_id = State()


class BillNavigator:

    @staticmethod
    async def get_current_bills() -> Optional[List]:
        return await bills_db.get_bills()
    
    @staticmethod
    async def format_bill_caption(bill, user) -> str:
        time_difference = datetime.datetime.now() - bill.created_at
        hours = int(time_difference.total_seconds() // 3600)
        minutes = int((time_difference.total_seconds() % 3600) // 60)
        return (
            f'<b>Студент:</b> <a href="https://t.me/{user.user_name}">{user.irl_name}</a>\n\n'
            f'<b>Отправлено:</b> {hours-8} часов {minutes} минут назад'
        )
    
    @staticmethod
    async def show_bill(chat_id: int, level: int, bills: List, message_to_edit=None):
        if not bills or level >= len(bills):
            if message_to_edit:
                await message_to_edit.delete()
            await BillNavigator.show_admin_panel(chat_id)
            return False
        current_bill = bills[level]
        user = await usr_db.user_exists(current_bill.user_id)
        caption = await BillNavigator.format_bill_caption(current_bill, user)
        keyboard = await BillNavigator.get_navigation_keyboard(
            bill_id=current_bill.id,
            level=level,
            total_bills=len(bills)
        )
        if current_bill.media_type == "photo":
            if message_to_edit:
                try:
                    await message_to_edit.edit_media(
                        media=InputMediaPhoto(
                            media=current_bill.media,
                            caption=caption,
                            parse_mode='HTML'
                        ),
                        reply_markup=keyboard
                    )
                except:
                    await message_to_edit.delete()
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=current_bill.media,
                        caption=caption,
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
            else:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=current_bill.media,
                    caption=caption,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
        elif current_bill.media_type == "doc":
            if message_to_edit:
                await message_to_edit.delete()
            await bot.send_document(
                chat_id=chat_id,
                document=current_bill.media,
                caption=caption,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        return True
    
    @staticmethod
    async def get_navigation_keyboard(bill_id: int, level: int, total_bills: int):
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="❌", 
                callback_data=ProBillsAction(
                    action="deny",
                    level=level,  
                    bill_id=bill_id
                ).pack()
            ),
            InlineKeyboardButton(
                text="✔️",
                callback_data=ProBillsAction(
                    action="accept",
                    level=level,  
                    bill_id=bill_id
                ).pack()
            )
        )
        nav_buttons = []
        if level > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⬅",
                    callback_data=BillsAction(
                        action="prev",
                        level=level,
                        bill_id=bill_id
                    ).pack()
                )
            )
        nav_buttons.append(
            InlineKeyboardButton(
                text="Выйти",
                callback_data=BillsAction(
                    action="exit",
                    level=level,
                    bill_id=bill_id
                ).pack()
            )
        )
        if level < total_bills - 1:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="➡",
                    callback_data=BillsAction(
                        action="next",
                        level=level,
                        bill_id=bill_id
                    ).pack()
                )
            )
        if nav_buttons:
            builder.row(*nav_buttons)
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

@router.callback_query(AdminActions.filter(F.action=="check_bills"))
async def start_bills_review(callback: CallbackQuery, callback_data: AdminActions, state: FSMContext):
    chat_id = callback.from_user.id
    bills = await BillNavigator.get_current_bills()
    if not bills:
        await callback.message.delete()
        await bot.send_message(chat_id=chat_id, text="Чеков нет")
        await BillNavigator.show_admin_panel(chat_id)
        return
    await state.set_state(BillListing.current_level)
    await state.update_data(current_level=0)
    await callback.message.delete()
    success = await BillNavigator.show_bill(chat_id, 0, bills)
    if success:
        await state.update_data(bills_message_id=callback.message.message_id)

@router.callback_query(BillsAction.filter())
async def handle_navigation(callback: CallbackQuery, callback_data: BillsAction, state: FSMContext):
    chat_id = callback.from_user.id
    if callback_data.action == "exit":
        await callback.message.delete()
        await state.clear()
        await BillNavigator.show_admin_panel(chat_id)
        return
    state_data = await state.get_data()
    current_level = state_data.get("current_level", 0)
    if callback_data.action == "next":
        current_level += 1
    elif callback_data.action == "prev":
        current_level -= 1
    bills = await BillNavigator.get_current_bills()
    if not bills or current_level >= len(bills) or current_level < 0:
        await callback.message.delete()
        await state.clear()
        await BillNavigator.show_admin_panel(chat_id)
        return
    await state.update_data(current_level=current_level)
    await BillNavigator.show_bill(chat_id, current_level, bills, callback.message)

@router.callback_query(ProBillsAction.filter())
async def handle_bill_action(callback: CallbackQuery, callback_data: ProBillsAction, state: FSMContext):
    chat_id = callback.from_user.id
    state_data = await state.get_data()
    current_level = state_data.get("current_level", callback_data.level)
    if callback_data.action == "deny":
        await bills_db.archive_bill(callback_data.bill_id, 'Denied')
        bills = await BillNavigator.get_current_bills()
        if not bills:
            await callback.message.delete()
            await state.clear()
            await bot.send_message(chat_id=chat_id, text="Все чеки обработаны")
            await BillNavigator.show_admin_panel(chat_id)
            return
        if current_level >= len(bills):
            current_level = len(bills) - 1
        await state.update_data(current_level=current_level)
        await BillNavigator.show_bill(chat_id, current_level, bills, callback.message)
    elif callback_data.action == "accept":
        await state.set_state(BillListing.bill_size)
        await state.update_data(
            pending_bill_id=callback_data.bill_id,
            bills_message_id=callback.message.message_id
        )
        sent_message = await callback.message.answer(
            text=await db.get_desc("bill_size"),
            parse_mode='HTML'
        )
        await state.update_data(money_message_id=sent_message.message_id)

@router.message(BillListing.bill_size, F.text)
async def process_bill_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму (число)")
        return
    state_data = await state.get_data()
    bill_id = state_data.get("pending_bill_id")
    money_message_id = state_data.get("money_message_id")
    bills_message_id = state_data.get("bills_message_id")
    current_level = state_data.get("current_level", 0)
    await bot.delete_message(chat_id=message.chat.id, message_id=money_message_id)
    await message.delete()
    bills = await BillNavigator.get_current_bills()
    await usr_db.pay_up(bills[current_level].user_id, amount)
    await bills_db.archive_bill(bill_id, 'Accepted')
    bills = await BillNavigator.get_current_bills()
    if not bills:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=bills_message_id)
        except:
            pass
        await state.clear()
        await bot.send_message(chat_id=message.chat.id, text="Все чеки обработаны")
        await BillNavigator.show_admin_panel(message.chat.id)
        return
    if current_level >= len(bills):
        current_level = len(bills) - 1
    await state.set_state(BillListing.current_level)
    await state.update_data(current_level=current_level)
    try:
        await bot.delete_message(message.chat.id, bills_message_id)
        await BillNavigator.show_bill(message.chat.id, current_level, bills)
    except:
        await BillNavigator.show_bill(message.chat.id, current_level, bills)