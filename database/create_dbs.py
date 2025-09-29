import asyncio 
import os
import sys
from queries.orm import PnDs, Users, Bills

pictures = PnDs()
users = Users()
bills = Bills()

async def popop():
    await pictures.create_tables()
    await users.create_tables()
    await bills.create_tables()

asyncio.run(popop())