import discord
from discord.ext import commands
from dotenv import load_dotenv
import aiosqlite
import os
load_dotenv()

class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = None
        self.c = None
        
        # Ensure "database" folder exists
        if not os.path.exists("database"):
            os.makedirs("database")
        
        self.bot.loop.create_task(self.load_db())

    async def load_db(self):
        try:
            sqlite_db = os.path.join("database", os.getenv('SQLITEDB'))
            print(f"Attempting to connect to database at: {sqlite_db}")  # Debug print
            self.conn = await aiosqlite.connect(sqlite_db)
            self.c = await self.conn.cursor()
            print("Connected to database successfully!")  # Debug print
            for guild in self.bot.guilds:
                await self.setup_database(guild.id)
        except Exception as e:
            print(f"Error connecting to SQLite database: {e}")


    async def setup_database(self, guild_id):
        try:
            # Setup table for FAQs
            await self.c.execute(f"""
                CREATE TABLE IF NOT EXISTS faqs_{guild_id}(
                    number INTEGER PRIMARY KEY,
                    content TEXT
                )
            """)
            # Setup table for user post timestamps in the showcase channel
            await self.c.execute(f"""
                CREATE TABLE IF NOT EXISTS showcase_{guild_id}(
                    user_id INTEGER PRIMARY KEY,
                    last_post_time FLOAT
                )
            """)
            # Setup table for server roles
            await self.c.execute(f"""
                CREATE TABLE IF NOT EXISTS serverroles_{guild_id}(
                    predefined_name TEXT PRIMARY KEY,
                    role_name TEXT,
                    role_id INTEGER
                )
            """)
            
            # Insert default role names into the table
            role_names = [
                "Read the Rules",
                "Patreon Announcements",
                "Announcements",
                "Behind the Scenes",
                "Showcase"
            ]
            for name in role_names:
                await self.c.execute(f"INSERT OR IGNORE INTO serverroles_{guild_id}(predefined_name) VALUES (?)", (name,))
            
            # Setup table for votes
            await self.c.execute(f"""
                CREATE TABLE IF NOT EXISTS votes(
                    post_id INTEGER,
                    user_id INTEGER,
                    PRIMARY KEY(post_id, user_id)
                )
            """)
            
            await self.conn.commit()
        except Exception as e:
            print(f"Error setting up database: {e}")

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

    async def set_server_role(self, guild_id, predefined_name, role_name, role_id):
        try:
            await self.c.execute(f"""
                INSERT OR REPLACE INTO serverroles_{guild_id}(predefined_name, role_name, role_id)
                VALUES (?, ?, ?)
            """, (predefined_name, role_name, role_id))
            await self.conn.commit()
            print(f"Linked role: {role_name} with ID: {role_id} To predefined role: {predefined_name}")
        except Exception as e:
            print(f"Error setting server role: {e}")

    async def get_all_faqs(self, guild_id):
        await self.c.execute(f"SELECT number, content FROM faqs_{guild_id}")
        data = await self.c.fetchall()
        return data
    
    async def get_server_role(self, guild_id, predefined_name):
        await self.c.execute(f"SELECT role_id FROM serverroles_{guild_id} WHERE predefined_name = ?", (predefined_name,))
        data = await self.c.fetchone()
        
        if data:
            return data[0]  # Return the role_id
        return None

    async def get_predefined_role_names(self, guild_id):
        """Fetch predefined role names from the serverroles table for a specific guild."""
        await self.c.execute(f"SELECT predefined_name FROM serverroles_{guild_id}")
        data = await self.c.fetchall()

        if data:
            # Return a list of role names
            return [entry[0] for entry in data]
        return []


    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.setup_database(guild.id)

async def setup(bot):
    await bot.add_cog(Database(bot))
