import asyncio
import sql


async def initdb():
    tables = [table["table_name"] for table in await sql.fetch("SELECT table_name FROM information_schema.tables")]
    if "servers" not in tables:
        await sql.execute("CREATE TABLE servers (serverid varchar(20) PRIMARY KEY, joinleavechannel varchar(20), comment text)")
    if "faq" not in tables:
        await sql.execute("CREATE TABLE faq (serverid varchar(20), title text, content text, image text, creator varchar(20), timestamp timestamptz, link text)")
    if "prefixes" not in tables:
        await sql.execute("CREATE TABLE prefixes (serverid varchar(20), prefix text)")
    if "modroles" not in tables:
        await sql.execute("CREATE TABLE modroles (serverid varchar(20), roleid varchar(20))")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(initdb())
    loop.close()
