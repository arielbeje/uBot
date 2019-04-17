import aiosqlite
import json
import logging
from typing import List, Tuple, Union

DB_FILE = "db.db"

logger = logging.getLogger('root')


class InvalidQueryError(Exception):
    pass


class NoDBError(Exception):
    pass


with open("data/defaults.json") as f:
    defaults = json.load(f)


async def execute(query: str, *args: str):
    """
    Executes the given query + args in the database
    """
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(query, args)
        await db.commit()


async def fetch(query: str, *args: str) -> Union[List[Tuple[str]], None]:
    """
    Returns the result from the given query + args in the database
    """
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(query, args)
        rows = await cursor.fetchall()
    return rows


async def executemany_queries(*queries: str):
    """
    Executes many queries utilizing only one session
    """
    async with aiosqlite.connect(DB_FILE) as db:
        for query in queries:
            if type(query) == tuple:
                await db.execute(query[0], query[1:])
                await db.commit()
            elif type(query) == str:
                await db.execute(query)
                await db.commit()
            else:
                raise InvalidQueryError()


async def initserver(serverid: Union[int, str]):
    """
    Initializes the values in the database for the given server ID
    """
    await executemany_queries(
        ("INSERT INTO servers (serverid, comment) VALUES (?, ?)", str(serverid), defaults["comment"]),
        ("INSERT INTO prefixes VALUES (?, ?)", str(serverid), defaults["prefix"])
    )


async def deleteserver(serverid: Union[int, str]):
    """
    Removes all lines refrencing the given server ID from the database
    """
    queries = ["DELETE FROM servers WHERE serverid=?",
               "DELETE FROM prefixes WHERE serverid=?",
               "DELETE FROM faq WHERE serverid=?",
               "DELETE FROM modroles WHERE serverid=?"]
    await executemany_queries(*[(query, str(serverid)) for query in queries])
