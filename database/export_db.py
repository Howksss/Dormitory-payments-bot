from sqlalchemy.ext.asyncio import create_async_engine
import pandas as pd
import asyncio
from database.config import settings

# Подключение к БД
async_engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=False,
    pool_size=5,
    max_overflow=10
)

async def export_to_excel():
    try:
        async with async_engine.begin() as conn:
            df = await conn.run_sync(
                lambda sync_conn: pd.read_sql("SELECT * FROM users", sync_conn)
            )
        if "paying_status" in df.columns:
            df["paying_status"] = pd.to_numeric(df["paying_status"], errors="coerce").fillna(0).astype(float)
            df = df[df["paying_status"] < 0]
        if "irl_name" in df.columns:
            df = df.sort_values(by="irl_name", ascending=True)
        output_file = "database/exported_users.xlsx"
        df.to_excel(output_file, index=False)
        print(f"Успешно выгрузил {len(df)} строк в файл {output_file}")
        return True
    except Exception as e:
        print(f"Ошибка при экспорте: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(export_to_excel())
