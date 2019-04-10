import aiosqlite
import json
import logging

DB_FILE = "db.db"

logger = logging.getLogger('root')


class InvalidQueryError(Exception):
    pass


class NoDBError(Exception):
    pass


with open("data/defaults.json") as f:
    defaults = json.load(f)


async def execute(query, *args):
    async with aiosqlite.connect(DB_FILE) as db:
        if args:
            await db.execute(query, args)
        else:
            await db.execute(query)
        await db.commit()


async def fetch(query, *args):
    async with aiosqlite.connect(DB_FILE) as db:
        cursor = await db.execute(query, args)
        rows = await cursor.fetchall()
    return rows


async def executemany(query, *args):
    # TODO: Add conversions
    async with aiosqlite.connect(DB_FILE) as db:
        await db.executemany(query, *args)


async def executemany_queries(*queries):
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


async def initserver(serverid):
    await executemany_queries(
        ("INSERT INTO servers (serverid, comment) VALUES (?, ?)", str(serverid), defaults["comment"]),
        ("INSERT INTO prefixes VALUES (?, ?)", str(serverid), defaults["prefix"])
    )


async def deleteserver(serverid):
    queries = ["DELETE FROM servers WHERE serverid=?",
               "DELETE FROM prefixes WHERE serverid=?",
               "DELETE FROM faq WHERE serverid=?",
               "DELETE FROM modroles WHERE serverid=?"]
    await executemany_queries(*[(query, str(serverid)) for query in queries])
