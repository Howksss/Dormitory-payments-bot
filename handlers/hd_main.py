from aiogram import Router, F, Bot
from aiogram.types import Message
from dotenv import load_dotenv
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from database.queries.orm import PnDs, Users, Bills
from keyboards.kb_main import Movements, tabs, main_tabs, MainMovements
from keyboards.kb_admin import admin_use
from aiogram.fsm.context import FSMContext
from database.config import settings
from aiogram.types import FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InputMediaPhoto, InputMediaDocument
import os 
import datetime
from ast import literal_eval

load_dotenv()
router = Router()
db = PnDs() 
usr_db = Users()
bills_db = Bills()
bot = Bot(settings.TOKEN)


class Verification(StatesGroup):
    name = State()
    contract = State()
    empty = State()

class BillsSending(StatesGroup):
    file = State()
    media_type = State()


@router.message(Command("start"))
async def id_command(message: Message, state: FSMContext):
    print(message.from_user.id)
    print(os.getenv("ADMIN"))
    if message.from_user.id == int(os.getenv('ADMIN')):
        await message.answer_photo(photo = await db.get_pic("admin_panel_0"),caption=await db.get_desc("admin_panel_0"), parse_mode = 'HTML', reply_markup = await admin_use(0))
    elif await usr_db.user_exists(message.from_user.id) == False:
        await state.clear()
        await state.set_state(Verification.name)
        await message.answer(text=await db.get_desc("verif_user_0"),
        parse_mode='HTML')
    else:
        user = await usr_db.user_exists(message.from_user.id)
        await message.answer_photo(photo=await db.get_pic('main_table_0'), caption=f'<b>Имя:</b> {user.irl_name}\n{user.contract}\n\n<b>Остаток:</b> {user.paying_status}р\n\n<b>Дней до выселения: </b>{(user.contract_exp_date - datetime.datetime.now()).days}',
        parse_mode='HTML', reply_markup = await main_tabs(0, 'main_table'))

@router.message(Verification.name, F.text)
async def verif_handler(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Verification.contract)
    await message.answer(text=f'Твоё имя: {message.text}\n\n{await db.get_desc("verif_user_1")}',
        parse_mode='HTML', reply_markup=await tabs(stage = "verif_user", level = 1))
    await state.set_state(Verification.contract)

@router.message(Verification.contract, F.text)
async def verif_handler(message: Message, state: FSMContext):
    await state.update_data(contract=message.text)
    user_data = await state.get_data()
    await state.set_state(Verification.empty)
    await message.answer(text=f'Твоё имя: {user_data["name"]}\n\nНомер твоего договора: {message.text}\n\n{await db.get_desc("verif_user_2")}',
        parse_mode='HTML', reply_markup=await tabs(stage = "verif_user", level = 2))

@router.callback_query(Movements.filter(F.placement == "verif_user"))
async def verif_handler(callback: CallbackQuery, callback_data: Movements, state: FSMContext):
    match callback_data.level:
        case 0:
            await state.set_data({})
            await state.set_state(Verification.name)
            await callback.message.edit_text(text=await db.get_desc("verif_user_0"),
            parse_mode='HTML')
        case 1:
            await state.update_data(contract="")
            await state.set_state(Verification.contract)
            user_data = await state.get_data()
            await callback.message.edit_text(text=f'Твоё имя: {user_data["name"]}\n\n{await db.get_desc(f"{callback_data.placement}_{callback_data.level}")}',
            parse_mode='HTML', reply_markup=await tabs(callback_data.level,callback_data.placement))
        case 3:
            user_data = await state.get_data()
            res = await usr_db.verif_user(user_data['contract'], user_data['name'], callback.from_user.id, callback.from_user.username)
            await state.clear()
            if res != False:
                user = await usr_db.user_exists(callback.from_user.id)
                await callback.message.delete()
                await bot.send_photo(chat_id = callback.message.chat.id, photo=await db.get_pic('main_table_0'), caption=f'<b>Имя:</b> {user.irl_name}\n{user.contract}\n\n<b>Остаток:</b> {user.paying_status}р\n\n<b>Дней до выселения: </b>{(user.contract_exp_date - datetime.datetime.now()).days}',
        parse_mode='HTML', reply_markup = await main_tabs(0, 'main_table'))
            else: 
                await state.set_state(Verification.name)
                chat_id = callback.message.chat.id
                await callback.message.delete()
                await bot.send_message(chat_id=chat_id, text = "Такой пользователь не найден или уже авторизован\nПопробуйте еще раз",
                parse_mode='HTML')
                await bot.send_message(chat_id = chat_id, text=await db.get_desc("verif_user_0"),
                parse_mode='HTML')
                 

@router.message(BillsSending.file, F.photo | F.document)
async def dudu(message: Message, state: FSMContext):
    if message.photo:
        await state.update_data(file=message.photo[-1].file_id) 
        await state.update_data(media_type="photo")
    elif message.document:
        await state.update_data(file=message.document.file_id)
        await state.update_data(media_type="doc")
    await message.reply(text=await db.get_desc("main_table_2"),
        parse_mode='HTML', reply_markup=await main_tabs(stage = "main_table", level = 2))



@router.callback_query(MainMovements.filter())
async def verif_handler(callback: CallbackQuery, callback_data: MainMovements, state: FSMContext):
    match callback_data.level:
        case 0:
            await state.clear()
            user = await usr_db.user_exists(callback.from_user.id)
            await callback.message.delete()
            await bot.send_photo(chat_id = callback.message.chat.id, photo=await db.get_pic('main_table_0'), caption=f'<b>Имя:</b> {user.irl_name}\n{user.contract}\n\n<b>Остаток:</b> {user.paying_status}р\n\n<b>Дней до выселения: </b>{(user.contract_exp_date - datetime.datetime.now()).days}',
            parse_mode='HTML', reply_markup = await main_tabs(0, 'main_table'))
        case 1:
            await state.clear()
            await state.set_state(BillsSending.file)
            chat_id = callback.message.chat.id
            await callback.message.delete()
            await bot.send_message(chat_id = chat_id, text=f'{await db.get_desc(f"{callback_data.placement}_{callback_data.level}")}',
            parse_mode='HTML', reply_markup=await main_tabs(callback_data.level,callback_data.placement))
        case 3:
            file_data = await state.get_data()
            await bills_db.add_bill(file_data["file"], callback.from_user.id, file_data["media_type"])
            await state.clear()
            user = await usr_db.user_exists(callback.from_user.id)
            chat_id = callback.message.chat.id
            await callback.message.delete()
            await bot.send_message(chat_id=chat_id, text = "Чек был успешно отправлен на проверку",
            parse_mode='HTML')
            await bot.send_photo(chat_id = callback.message.chat.id, photo=await db.get_pic('main_table_0'), caption=f'<b>Имя:</b> {user.irl_name}\n{user.contract}\n\n<b>Остаток:</b> {user.paying_status}р\n\n<b>Дней до выселения: </b>{(user.contract_exp_date - datetime.datetime.now()).days}',
            parse_mode='HTML', reply_markup = await main_tabs(0, 'main_table'))
