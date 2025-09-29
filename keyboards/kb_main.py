from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton  
from database.queries.orm import PnDs

db = PnDs()


#Коллбек-класс основного роутера
class Movements(CallbackData, prefix = ' 1'):
    placement: str
    level: int

class MainMovements(CallbackData, prefix = '9'):
    placement: str
    level: int


#Функция, возвращающая клавиатуры в зависимости от страницы level.
async def tabs(level,stage):
    match level:
        case 1:
            print(f'Клава на {stage}')
            builder=InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="Назад", callback_data=Movements(placement=stage, level = level-1).pack()))
            return builder.as_markup()
        case 2: 
            print(f'Клава на {stage}')
            builder=InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="Назад", callback_data=Movements(placement=stage, level = level-1).pack()),
                        InlineKeyboardButton(text="Подтвердить", callback_data=Movements(placement=stage, level = level+1).pack()))
            return builder.as_markup()
    
async def main_tabs(level, stage):
    match level:
        case 0:
            print(f'Клава на {stage}')
            builder=InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="Отправить чек", callback_data=MainMovements(placement=stage, level = level+1).pack()))
            return builder.as_markup()
        case 1: 
            print(f'Клава на {stage}')
            builder=InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="Назад", callback_data=MainMovements(placement=stage, level = level-1).pack()))
            return builder.as_markup()
        case 2:
            print(f'Клава на {stage}')
            builder=InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="Назад", callback_data=MainMovements(placement=stage, level = level-1).pack()),
                        InlineKeyboardButton(text="Подтвердить", callback_data=MainMovements(placement=stage, level = level+1).pack()))
            return builder.as_markup()