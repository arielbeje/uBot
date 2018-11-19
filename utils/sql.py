import asyncpg
import datetime
import json
import os
import logging

logger = logging.getLogger('root')


class NoCredentialsError(Exception):
    pass


class CouldntConnectError(Exception):
    pass


class InvalidQueryError(Exception):
    pass


class NoDBError(Exception):
    pass


if "UBOTPGPWD" not in os.environ or "UBOTPGUSR" not in os.environ:
    logger.critical("Couldn't find a Postgres username/password. Please enter them in the UBOTPGUSR/UBOTPGPWD environment variables respectively. "
                    "The bot will not run without them")
    raise NoCredentialsError()

if "UBOTPGDB" not in os.environ or "UBOTPGHOST" not in os.environ:
    logger.critical("Couldn't find Postgres DB to use. Please enter its details (name/host) in the UBOTPGDB/UBOTPGHOST environment variables. "
                    "The bot will not run without it")
    raise NoDBError()

connDetails = {"database": os.environ["UBOTPGDB"],
               "user": os.environ["UBOTPGUSR"],
               "host": os.environ["UBOTPGHOST"],
               "password": os.environ["UBOTPGPWD"]}

with open("data/defaults.json") as f:
    defaults = json.load(f)


async def execute(query, *args):
    conn = await asyncpg.connect(**connDetails)
    convertedArgs = []
    for arg in args:
        if not isinstance(arg, datetime.datetime) and arg is not None:
            convertedArgs.append(str(arg))
        else:
            convertedArgs.append(arg)
    await conn.execute(query, *convertedArgs)
    await conn.close()


async def fetch(query, *args):
    conn = await asyncpg.connect(**connDetails)
    convertedArgs = []
    for arg in args:
        if not isinstance(arg, datetime.datetime) and arg is not None:
            convertedArgs.append(str(arg))
        else:
            convertedArgs.append(arg)
    value = await conn.fetch(query, *convertedArgs)
    await conn.close()
    return value


async def executemany(query, *args):
    conn = await asyncpg.connect(**connDetails)
    # TODO: Add conversions
    await conn.executemany(query, *args)
    await conn.close()


async def executemany_queries(*queries):
    conn = await asyncpg.connect(**connDetails)
    for query in queries:
        if type(query) == tuple:
            # TODO: Add conversions
            await conn.execute(query[0], *query[1:])
        elif type(query) == str:
            await conn.execute(query)
        else:
            raise InvalidQueryError()
    await conn.close()


async def initserver(serverid):
    await executemany_queries(
        ("INSERT INTO servers (serverid, comment) VALUES ($1, $2)", str(serverid), defaults["comment"]),
        ("INSERT INTO prefixes VALUES ($1, $2)", str(serverid), defaults["prefix"])
    )


async def deleteserver(serverid):
    queries = ["DELETE FROM servers WHERE serverid=$1",
               "DELETE FROM prefixes WHERE serverid=$1",
               "DELETE FROM faq WHERE serverid=$1",
               "DELETE FROM modroles WHERE serverid=$1"]
    conn = await asyncpg.connect(**connDetails)
    for query in queries:
        await conn.execute(query, serverid)
    await conn.close()
