from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton 

class AdminActions(CallbackData, prefix = '2'):
    action: str
    level: int

class BillsAction(CallbackData, prefix = '5'):
    bill_id: int
    action: str
    level: int

class ProBillsAction(CallbackData, prefix='11'):
    bill_id: int
    action: str
    level: int

class AnnualPayActions(CallbackData, prefix='333'):
    action: str
    level: int

class ManagingActions(CallbackData, prefix='1717'):
    action: str
    level: int

async def admin_use(level,stage="admin_panel"):
    match level:
        case 0:
            builder=InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="Управление студентами", callback_data=AdminActions(action="manage_users", level=1).pack()))
            builder.row(InlineKeyboardButton(text="Проверка чеков", callback_data=AdminActions(action="check_bills", level=1).pack()))
            builder.row(InlineKeyboardButton(text="Ежемесячн. оплата", callback_data=AdminActions(action="annual_pay", level=1).pack()))
            builder.row(InlineKeyboardButton(text="Экспорт данных", callback_data=AdminActions(action="export", level = 1).pack()))
            return builder.as_markup()
        
