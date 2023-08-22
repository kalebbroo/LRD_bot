import discord
from discord.ext import commands
from dotenv import load_dotenv
import aiosqlite
import os
load_dotenv()

class Database(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.conn = None
        self.c = None
        
        # Check if "database" folder exists, if not, create it
        if not os.path.exists("database"):
            os.makedirs("database")
        
        self.bot.loop.create_task(self.load_db())

    async def load_db(self):
        try:
            sqlite_db = os.path.join("database", os.getenv('SQLITEDB'))
            self.conn = await aiosqlite.connect(sqlite_db)
            self.c = await self.conn.cursor()
        except Exception as e:
            print(f"Error connecting to SQLite database: {e}")

    async def setup_database(self, guild_id):
        conn = await aiosqlite.connect(os.getenv('SQLITEDB'))
        c = await conn.cursor()

        try:
            # Setup table for FAQs
            await c.execute(f"""
                CREATE TABLE IF NOT EXISTS faqs_{guild_id}(
                    number INTEGER PRIMARY KEY,
                    content TEXT
                )
            """)
            # Setup table for user post timestamps in the showcase channel
            await c.execute(f"""
                CREATE TABLE IF NOT EXISTS showcase_{guild_id}(
                    user_id INTEGER PRIMARY KEY,
                    last_post_time FLOAT
                )
            """)
            await conn.commit()
        except Exception as e:
            print(f"Error setting up database for guild {guild_id}: {e}")

        await conn.close()

    async def get_faq(self, number, guild_id):
        await self.c.execute(f"SELECT content FROM faqs_{guild_id} WHERE number = ?", (number,))
        data = await self.c.fetchone()

        if data:
            return data[0]
        return None

    async def add_faq(self, number, content, guild_id):
        await self.c.execute(f"INSERT INTO faqs_{guild_id}(number, content) VALUES (?, ?)", (number, content))
        await self.conn.commit()

    async def remove_faq(self, number, guild_id):
        await self.c.execute(f"DELETE FROM faqs_{guild_id} WHERE number = ?", (number,))
        await self.conn.commit()

    async def get_last_post_time(self, user_id, guild_id):
        await self.c.execute(f"SELECT last_post_time FROM showcase_{guild_id} WHERE user_id = ?", (user_id,))
        data = await self.c.fetchone()

        if data:
            return data[0]
        return None

    async def update_last_post_time(self, user_id, guild_id, timestamp):
        await self.c.execute(f"INSERT OR REPLACE INTO showcase_{guild_id}(user_id, last_post_time) VALUES (?, ?)", (user_id, timestamp))
        await self.conn.commit()

    async def close_db(self):
        await self.conn.close()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.setup_database(guild.id)

async def setup(bot:commands.Bot):
    db = Database(bot)
    await db.load_db()
    await bot.add_cog(db)
