from sqlalchemy import select
import datetime
from database.db_setup import async_engine, async_session, Base
from database.models import PnDsOrm, UserOrm, BillsOrm

#Класс общения с таблицей Pictures and Descriptions
class PnDs():


    #Стартовый метод создания всех таблиц, используется один раз
    @staticmethod
    async def create_tables():
        async_engine.echo = False
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async_engine.echo = True

    #Добавление данных о странице
    @staticmethod
    async def insert_data(stage_name, desc_content, pic_content):
        async with async_session() as s:  
            page = PnDsOrm(stage_name=stage_name, desc_content= desc_content, pic_content=pic_content)
            s.add(page)
            await s.commit()  
            await s.close()
        
    @staticmethod
    async def get_pic(stage_name):
        async with async_session() as s:
            caveat = select(PnDsOrm).where(PnDsOrm.stage_name == stage_name, PnDsOrm.pic_content != "")
            res = await s.execute(caveat)
            pic = res.scalar_one_or_none()
            return pic.pic_content or ""
        
    @staticmethod
    async def get_desc(stage_name):
        async with async_session() as s:
            caveat = select(PnDsOrm).where(PnDsOrm.stage_name == stage_name, PnDsOrm.desc_content != "")
            res = await s.execute(caveat)
            desc = res.scalar_one_or_none()
            return desc.desc_content or ""


#Класс общения с таблицей Users
class Users():

        #Стартовый метод создания всех таблиц, используется один раз
    @staticmethod
    async def create_tables():
        async_engine.echo = False
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async_engine.echo = True

    #Добавление нового пользователя в бд
    @staticmethod
    async def add_user(irl_name: str, contract: str, contract_exp_date: str, paying_status: str, user_id: int = 0, user_name: str = ""):
        async with async_session() as s:  
            user = UserOrm(irl_name=irl_name, contract=contract, contract_exp_date=contract_exp_date, paying_status=paying_status, user_id = user_id, user_name = user_name)
            s.add(user)
            await s.commit()  
            await s.close()  

    #Добавление позиции в бд тг-пользователя (авторизация)
    @staticmethod
    async def verif_user(_contract:str, _irl_name: str, user_id: int, user_name: str):
        async with async_session() as s:
            caveat=select(UserOrm).where(UserOrm.irl_name == _irl_name, UserOrm.contract ==  _contract)
            res = await s.execute(caveat)
            user = res.scalar_one_or_none()
            if user and user.user_id == 0:
                user.user_id = user_id
                user.user_name = user_name
                user.created_at = datetime.datetime.now()
                await s.commit()
                return True
            else:
                return False
            
    @staticmethod 
    async def delete_user(user_id: int):
        async with async_session() as s:
            caveat = select(UserOrm).where(UserOrm.user_id==user_id)
            res = await s.execute(caveat)
            user = res.scalar_one_or_none()
            name = user.irl_name
            if user:
                await s.delete(user)
                await s.commit()
                return f"Удалён пользователь {name}"
            else: return f"Пользователь не найден"
        
    @staticmethod
    async def annual_pay(summ:float):
        async with async_session() as s:
            caveat = select(UserOrm)
            res = await s.execute(caveat)
            users = res.scalars().all()
            if users:
                for user in users:
                    user.paying_status-=summ
                await s.commit()    
                return f"Успешно списано {summ} у всех пользователей"
            else: f'Не получилось изменить сумму у пользователей'

    @staticmethod
    async def pay_up(user_id:int, sum:float):
        async with async_session() as s:
            caveat = select(UserOrm).where(UserOrm.user_id==user_id)
            res = await s.execute(caveat)
            user = res.scalar_one_or_none()
            old_sum = user.paying_status
            if user:
                user.paying_status+=sum
                await s.commit()
                return f"У пользователя {user.irl_name} изменилась сумма\n\nБыло: {old_sum}\nСтало: {user.paying_status}"
            else: return f"Не получилось изменить сумму у пользователя {user.irl_name}"
            
            
    
    #Проверка, существует ли пользователь True/False
    @staticmethod
    async def user_exists(user_id: str):
        async with async_session() as s:
            caveat = select(UserOrm).where(UserOrm.user_id == user_id)
            res = await s.execute(caveat)
            user = res.scalar_one_or_none()
            return user or False
        
    @staticmethod
    async def update_user_field(contract, oper_type, data):
        async with async_session() as s:
            caveat = select(UserOrm).where(UserOrm.contract == contract)
            res = await s.execute(caveat)
            user = res.scalar_one_or_none()
            if not user: return False
            match oper_type:
                case "irl_name":
                    user.irl_name = str(data)
                    await s.commit()
                    return user
                case "contract":
                    user.contract = str(data)
                    await s.commit()
                    return user
                case "contract_exp_date":
                    user.contract_exp_date = data
                    await s.commit()
                    return user
                case "paying_status":
                    user.paying_status = float(data)
                    await s.commit()
                    return user


    @staticmethod
    async def find_user(contract: str):
        async with async_session() as s:
            caveat = select(UserOrm).where(UserOrm.contract == contract)
            res = await s.execute(caveat)
            user = res.scalar_one_or_none()
            return user or False
        
    #Получение всех пользователей, когда-либо запускавших бота
    @staticmethod
    async def all_users():
        async with async_session() as s:
            query = select(UserOrm)
            res = await s.execute(query)
            result = res.scalars().all()
            users = []
            for each in range(0, len(result)):
                users.append(result[each].user_id)     #Возвращает именно id
            print(users)

    


class Bills():
    #Стартовый метод создания всех таблиц, используется один раз
    @staticmethod
    async def create_tables():
        async_engine.echo = False
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async_engine.echo = True


    #Проверка, существует ли пользователь True/False
    @staticmethod
    async def get_bills():
        async with async_session() as s:
            caveat = select(BillsOrm).where(BillsOrm.status=="Waiting")
            res = await s.execute(caveat)
            bills = res.scalars().all()
            return bills or False


    @staticmethod
    async def add_bill(_media: str, user_id: int, media_type:str):
        async with async_session() as s:  
            bill = BillsOrm(media=_media, user_id = user_id, media_type=media_type, status = "Waiting")
            s.add(bill)
            await s.commit()  
            await s.close()

    @staticmethod 
    async def archive_bill(_id: str, _status):
        async with async_session() as s:
            caveat = select(BillsOrm).where(BillsOrm.id==_id)
            res = await s.execute(caveat)
            bill = res.scalar_one_or_none()
            bill.status = _status
            await s.commit()
            await s.close()

        