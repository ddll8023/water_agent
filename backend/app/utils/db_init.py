from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
from app.utils.file import ROOT_DIR
import os


import re


async def init_db(conn: AsyncConnection):
    with open(os.path.join(ROOT_DIR, "init_data.sql"), "r", encoding="utf-8") as f:
        sql = f.read()
    sql = re.sub(r":(?=\w)", r"\\:", sql)
    await conn.execute(text(sql))
