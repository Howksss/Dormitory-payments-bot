from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import Bot
from database.queries.orm import Users, PnDs, Bills
from keyboards.kb_admin import admin_use, BillsAction, AdminActions, ProBillsAction, ManagingActions
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from database.config import settings
import datetime
from typing import Optional, List, Dict, Any

router = Router()
bot = Bot(settings.TOKEN)
db = PnDs() 
usr_db = Users()
bills_db = Bills()

class UserInfo(StatesGroup):
    contract = State()
    confirm_delete = State()
    add_name = State()
    add_contract = State()
    add_exp_date = State()
    add_paying_status = State()
    edit_field = State()

class UserManaging:

    @staticmethod
    async def get_managing_keyboard(level: int):
        builder = InlineKeyboardBuilder()
        match level:
            case 1:  
                builder.row(
                    InlineKeyboardButton(text="Добавить", callback_data=ManagingActions(action="add", level=level).pack()),
                    InlineKeyboardButton(text="Управлять", callback_data=ManagingActions(action="manage", level=level).pack())
                )
                builder.row(InlineKeyboardButton(text="Назад", callback_data=ManagingActions(action="exit", level=level).pack()))
            case 2: 
                builder.row(
                    InlineKeyboardButton(text="Подтвердить", callback_data=ManagingActions(action="confirm", level=level).pack()),
                    InlineKeyboardButton(text="Назад", callback_data=ManagingActions(action="back", level=level).pack())
                )
            case 3:  
                builder.row(
                    InlineKeyboardButton(text="Удалить", callback_data=ManagingActions(action="delete", level=level).pack()),
                    InlineKeyboardButton(text="Редактировать", callback_data=ManagingActions(action="edit", level=level).pack())
                )
                builder.row(InlineKeyboardButton(text="Назад", callback_data=ManagingActions(action="back_to_main", level=level).pack()))
            case 4:  
                builder.row(
                    InlineKeyboardButton(text="Подтвердить", callback_data=ManagingActions(action="confirm_delete", level=level).pack()),
                    InlineKeyboardButton(text="Назад", callback_data=ManagingActions(action="cancel_delete", level=level).pack())
                )
            case 5: 
                builder.row(
                    InlineKeyboardButton(text="Подтвердить", callback_data=ManagingActions(action="confirm_input", level=level).pack()),
                    InlineKeyboardButton(text="Назад", callback_data=ManagingActions(action="back_input", level=level).pack())
                )
            case 6:  
                builder.row(
                    InlineKeyboardButton(text="ФИО", callback_data=ManagingActions(action="edit_name", level=level).pack()),
                    InlineKeyboardButton(text="Номер договора", callback_data=ManagingActions(action="edit_contract", level=level).pack())
                )
                builder.row(
                    InlineKeyboardButton(text="Дата окончания", callback_data=ManagingActions(action="edit_exp_date", level=level).pack()),
                    InlineKeyboardButton(text="Сумма счета", callback_data=ManagingActions(action="edit_paying_status", level=level).pack())
                )
                builder.row(InlineKeyboardButton(text="Назад", callback_data=ManagingActions(action="back_to_user", level=level).pack()))

        return builder.as_markup()
    
    @staticmethod
    async def get_back_only_keyboard():
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="Назад", callback_data=ManagingActions(action="back_input", level=5).pack()))
        return builder.as_markup()
    
    @staticmethod
    def parse_date(date_str: str) -> datetime.datetime:
        try:
            day, month, year = date_str.split('.')
            return datetime.datetime(int(year), int(month), int(day))
        except (ValueError, AttributeError):
            raise ValueError("Invalid date format")
    
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
    async def show_user_info(chat_id: int, user: Any):
        days_until_expiry = (user.contract_exp_date - datetime.datetime.now()).days
        await bot.send_photo(
            chat_id=chat_id,
            photo=await db.get_pic("main_table_0"),
            caption=f'<b>Имя:</b> {user.irl_name}\n{user.contract}\n\n<b>Остаток:</b> {user.paying_status}р\n\n<b>Дней до выселения: </b>{days_until_expiry}',
            parse_mode='HTML',
            reply_markup=await UserManaging.get_managing_keyboard(3)
        )

@router.callback_query(ManagingActions.filter())
async def handle_managing(callback: CallbackQuery, callback_data: ManagingActions, state: FSMContext):
    chat_id = callback.from_user.id
    state_data = await state.get_data()
    action = callback_data.action
    
    await callback.message.delete()
    
    if action == "exit":
        await state.clear()
        await UserManaging.show_admin_panel(chat_id)
        return
        
    elif action in ["back", "back_to_main"]:
        await state.clear()
        await bot.send_message(
            chat_id,
            text=await db.get_desc("manage_users_1"),
            parse_mode='HTML',
            reply_markup=await UserManaging.get_managing_keyboard(1)
        )
        return
    
    elif action == "manage":
        await state.set_state(UserInfo.contract)
        await bot.send_message(
            chat_id,
            text="Введите номер Договора пользователя",
            parse_mode='HTML',
            reply_markup=await UserManaging.get_back_only_keyboard()
        )
        
    elif action == "confirm":
        contract = state_data.get("contract")
        user = await usr_db.find_user(contract)
        
        if not user:
            await bot.send_message(chat_id, text=await db.get_desc("manage_users_failed"), parse_mode='HTML')
            await UserManaging.show_admin_panel(chat_id)
            await state.clear()
            return
            
        await state.update_data(current_user=user)
        await UserManaging.show_user_info(chat_id, user)
    
    elif action == "edit":
        await bot.send_message(
            chat_id,
            text="Выберите, какой параметр хотите изменить",
            parse_mode='HTML',
            reply_markup=await UserManaging.get_managing_keyboard(6)
        )
        
    elif action == "edit_name":
        await state.update_data(editing_field="name")
        await state.set_state(UserInfo.edit_field)
        await bot.send_message(
            chat_id,
            text="Введите новое ФИО пользователя в следующем формате:\n\nИванов Иван Иванович",
            parse_mode='HTML',
            reply_markup=await UserManaging.get_back_only_keyboard()
        )
        
    elif action == "edit_contract":
        await state.update_data(editing_field="contract")
        await state.set_state(UserInfo.edit_field)
        await bot.send_message(
            chat_id,
            text="Введите новый номер Договора в следующем формате:\n\nДоговор от 00.00.0000 № 000/0/00",
            parse_mode='HTML',
            reply_markup=await UserManaging.get_back_only_keyboard()
        )
        
    elif action == "edit_exp_date":
        await state.update_data(editing_field="exp_date")
        await state.set_state(UserInfo.edit_field)
        await bot.send_message(
            chat_id,
            text="Введите новую дату окончания Договора в формате: ДД.ММ.ГГГГ",
            parse_mode='HTML',
            reply_markup=await UserManaging.get_back_only_keyboard()
        )
        
    elif action == "edit_paying_status":
        await state.update_data(editing_field="paying_status")
        await state.set_state(UserInfo.edit_field)
        await bot.send_message(
            chat_id,
            text="Введите новую сумму счета в следующем формате:\n\n1350.02",
            parse_mode='HTML',
            reply_markup=await UserManaging.get_back_only_keyboard()
        )
        
    elif action == "back_to_user":
        user = state_data.get("current_user")
        if user:
            await UserManaging.show_user_info(chat_id, user)
    
    elif action == "delete":
        await state.set_state(UserInfo.confirm_delete)
        await bot.send_message(
            chat_id,
            text="Вы точно хотите удалить этого пользователя?",
            parse_mode='HTML',
            reply_markup=await UserManaging.get_managing_keyboard(4)
        )
        
    elif action == "confirm_delete":
        user = state_data.get("current_user")
        if user:
            await usr_db.delete_user(user.contract)
            await bot.send_message(chat_id, text="Пользователь успешно удален", parse_mode='HTML')
        await state.clear()
        await UserManaging.show_admin_panel(chat_id)
        
    elif action == "cancel_delete":
        user = state_data.get("current_user")
        if user:
            await UserManaging.show_user_info(chat_id, user)
    
    elif action == "add":
        await state.set_state(UserInfo.add_name)
        await bot.send_message(
            chat_id,
            text="Введите ФИО нового пользователя в следующем формате:\n\nИванов Иван Иванович",
            parse_mode='HTML',
            reply_markup=await UserManaging.get_back_only_keyboard()
        )
        
    elif action == "confirm_input":
        current_state = await state.get_state()
        if current_state == UserInfo.edit_field:
            field = state_data.get("editing_field")
            temp_value = state_data.get("temp_value")
            user = state_data.get("current_user")
            
            if user and temp_value:
                if field == "name":
                    await usr_db.update_user_field(user.contract, "irl_name", temp_value)
                elif field == "contract":
                    await usr_db.update_user_field(user.contract, "contract", temp_value)
                elif field == "exp_date":
                    date_obj = UserManaging.parse_date(temp_value)
                    await usr_db.update_user_field(user.contract, "contract_exp_date", date_obj)
                elif field == "paying_status":
                    await usr_db.update_user_field(user.contract, "paying_status", float(temp_value))
                
                await bot.send_message(chat_id, text="Данные успешно обновлены!", parse_mode='HTML')
                
                updated_user = await usr_db.find_user(user.contract if field != "contract" else temp_value)
                await state.update_data(current_user=updated_user)
                await UserManaging.show_user_info(chat_id, updated_user)

        elif current_state == UserInfo.add_name:
            if "temp_name" in state_data:
                await state.update_data(new_name=state_data["temp_name"])
                await state.set_state(UserInfo.add_contract)
                await bot.send_message(
                    chat_id,
                    text="Введите номер Договора",
                    parse_mode='HTML',
                    reply_markup=await UserManaging.get_back_only_keyboard()
                )
                
        elif current_state == UserInfo.add_contract:
            if "temp_contract" in state_data:
                await state.update_data(new_contract=state_data["temp_contract"])
                await state.set_state(UserInfo.add_exp_date)
                await bot.send_message(
                    chat_id,
                    text="Введите дату окончания Договора (формат: ДД.ММ.ГГГГ)",
                    parse_mode='HTML',
                    reply_markup=await UserManaging.get_back_only_keyboard()
                )
                
        elif current_state == UserInfo.add_exp_date:
            if "temp_exp_date" in state_data:
                await state.update_data(new_exp_date=state_data["temp_exp_date"])
                await state.set_state(UserInfo.add_paying_status)
                await bot.send_message(
                    chat_id,
                    text="Введите сумму счета",
                    parse_mode='HTML',
                    reply_markup=await UserManaging.get_back_only_keyboard()
                )
                
        elif current_state == UserInfo.add_paying_status:
            if "temp_paying_status" in state_data:
                exp_date = UserManaging.parse_date(state_data["new_exp_date"])
                
                await usr_db.add_user(
                    irl_name=state_data["new_name"],
                    contract=state_data["new_contract"],
                    contract_exp_date=exp_date,
                    paying_status=float(state_data["temp_paying_status"]),
                    user_id=0,
                    user_name=""
                )
                await bot.send_message(chat_id, text="Пользователь успешно добавлен!", parse_mode='HTML')
                await state.clear()
                await UserManaging.show_admin_panel(chat_id)
    
    elif action == "back_input":
        current_state = await state.get_state()
        
        if current_state == UserInfo.contract:
            await state.clear()
            await bot.send_message(
                chat_id,
                text=await db.get_desc("manage_users_1"),
                parse_mode='HTML',
                reply_markup=await UserManaging.get_managing_keyboard(1)
            )
        elif current_state == UserInfo.edit_field:
            await bot.send_message(
                chat_id,
                text="Выберите, какой параметр хотите изменить",
                parse_mode='HTML',
                reply_markup=await UserManaging.get_managing_keyboard(6)
            )
        elif current_state == UserInfo.add_name:
            await state.clear()
            await bot.send_message(
                chat_id,
                text=await db.get_desc("manage_users_1"),
                parse_mode='HTML',
                reply_markup=await UserManaging.get_managing_keyboard(1)
            )
        elif current_state == UserInfo.add_contract:
            await state.set_state(UserInfo.add_name)
            await bot.send_message(
                chat_id,
                text="Введите ФИО нового пользователя в следующем формате:\n\nИванов Иван Иванович",
                parse_mode='HTML',
                reply_markup=await UserManaging.get_back_only_keyboard()
            )
        elif current_state == UserInfo.add_exp_date:
            await state.set_state(UserInfo.add_contract)
            await bot.send_message(
                chat_id,
                text="Введите номер Договора",
                parse_mode='HTML',
                reply_markup=await UserManaging.get_back_only_keyboard()
            )
        elif current_state == UserInfo.add_paying_status:
            await state.set_state(UserInfo.add_exp_date)
            await bot.send_message(
                chat_id,
                text="Введите дату окончания Договора (формат: ДД.ММ.ГГГГ)",
                parse_mode='HTML',
                reply_markup=await UserManaging.get_back_only_keyboard()
            )

@router.message(UserInfo.contract)
async def handle_contract_input(message: Message, state: FSMContext):
    await state.update_data(contract=message.text)
    await message.delete()
    await bot.send_message(
        message.from_user.id,
        text=f"Договор: {message.text}\n\nПодтвердите корректность введенного договора",
        parse_mode='HTML',
        reply_markup=await UserManaging.get_managing_keyboard(2)
    )

@router.message(UserInfo.edit_field)
async def handle_edit_field(message: Message, state: FSMContext):
    chat_id = message.from_user.id
    state_data = await state.get_data()
    field = state_data.get("editing_field")
    value = message.text
    
    await message.delete()
    if field == "exp_date":
        try:
            UserManaging.parse_date(value)
        except (ValueError, TypeError):
            await bot.send_message(
                chat_id,
                text="Неверный формат даты\n\nВведите новую дату окончания Договора в формате: ДД.ММ.ГГГГ",
                parse_mode='HTML',
                reply_markup=await UserManaging.get_back_only_keyboard()
            )
            return
    
    if field == "paying_status":
        try:
            float(value)
        except (ValueError, TypeError):
            await bot.send_message(
                chat_id,
                text="Неверный формат суммы\n\nВведите новую сумму счета в следующем формате:\n\n1350.02",
                parse_mode='HTML',
                reply_markup=await UserManaging.get_back_only_keyboard()
            )
            return
    
    await state.update_data(temp_value=value)
    
    if field == "name":
        confirm_text = f"Новое ФИО: {value}\n\nПодтвердите корректность введенных данных"
    elif field == "contract":
        confirm_text = f"Новый Договор: {value}\n\nПодтвердите корректность введенных данных"
    elif field == "exp_date":
        confirm_text = f"Новая дата окончания: {value}\n\nПодтвердите корректность введенных данных"
    elif field == "paying_status":
        confirm_text = f"Новая сумма: {value}р\n\nПодтвердите корректность введенных данных"
    
    await bot.send_message(
        chat_id,
        text=confirm_text,
        parse_mode='HTML',
        reply_markup=await UserManaging.get_managing_keyboard(5)
    )

@router.message(UserInfo.add_name)
async def handle_add_name(message: Message, state: FSMContext):
    chat_id = message.from_user.id
    await state.update_data(temp_name=message.text)
    await message.delete()
    
    await bot.send_message(
        chat_id,
        text=f"ФИО: {message.text}\n\nПодтвердите ввод",
        parse_mode='HTML',
        reply_markup=await UserManaging.get_managing_keyboard(5)
    )

@router.message(UserInfo.add_contract)
async def handle_add_contract(message: Message, state: FSMContext):
    chat_id = message.from_user.id
    await state.update_data(temp_contract=message.text)
    await message.delete()
    
    await bot.send_message(
        chat_id,
        text=f"Договор: {message.text}\n\nПодтвердите ввод",
        parse_mode='HTML',
        reply_markup=await UserManaging.get_managing_keyboard(5)
    )

@router.message(UserInfo.add_exp_date)
async def handle_add_exp_date(message: Message, state: FSMContext):
    chat_id = message.from_user.id
    
    try:
        UserManaging.parse_date(message.text)
        await state.update_data(temp_exp_date=message.text)
        await message.delete()
        
        await bot.send_message(
            chat_id,
            text=f"Дата окончания: {message.text}\n\nПодтвердите ввод",
            parse_mode='HTML',
            reply_markup=await UserManaging.get_managing_keyboard(5)
        )
    except:
        await message.delete()
        await bot.send_message(
            chat_id,
            text="Неверный формат даты! Используйте формат ДД.ММ.ГГГГ (например: 31.12.2025)\n\nВведите дату окончания Договора",
            parse_mode='HTML',
            reply_markup=await UserManaging.get_back_only_keyboard()
        )

@router.message(UserInfo.add_paying_status)
async def handle_add_paying_status(message: Message, state: FSMContext):
    chat_id = message.from_user.id
    
    try:
        float(message.text)
        await state.update_data(temp_paying_status=message.text)
        await message.delete()
        
        await bot.send_message(
            chat_id,
            text=f"Сумма: {message.text}р\n\nПодтвердите ввод",
            parse_mode='HTML',
            reply_markup=await UserManaging.get_managing_keyboard(5)
        )
    except ValueError:
        await message.delete()
        await bot.send_message(
            chat_id,
            text="Неверный формат суммы! Введите число (например: 1200 или 1200.50)\n\nВведите сумму счета",
            parse_mode='HTML',
            reply_markup=await UserManaging.get_back_only_keyboard()
        )

@router.callback_query(AdminActions.filter(F.action == "manage_users"))
async def start_user_management(callback: CallbackQuery, callback_data: AdminActions, state: FSMContext):
    chat_id = callback.from_user.id
    await callback.message.delete()
    await state.clear()
    
    await bot.send_message(
        chat_id,
        text=await db.get_desc("manage_users_1"),
        parse_mode='HTML',
        reply_markup=await UserManaging.get_managing_keyboard(1)
    )