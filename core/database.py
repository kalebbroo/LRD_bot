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
            # Setup table for server roles
            await self.c.execute(f"""
                CREATE TABLE IF NOT EXISTS serverroles_{guild_id}(
                    button_name TEXT PRIMARY KEY,
                    role_name TEXT,
                    role_id INTEGER,
                    emoji TEXT
                )
            """)
            # Setup table for channels
            await self.c.execute(f"""
                CREATE TABLE IF NOT EXISTS channelmapping_{guild_id}(
                    channel_display_name TEXT PRIMARY KEY,
                    channel_name TEXT,
                    channel_id INTEGER,
                    message TEXT
                )
            """)
            # Setup table for votes
            await self.c.execute(f"""
                CREATE TABLE IF NOT EXISTS votes(
                    post_id INTEGER,
                    user_id INTEGER,
                    PRIMARY KEY(post_id, user_id)
                )
            """)
            # Setup table for user info
            await self.c.execute(f"""
                CREATE TABLE IF NOT EXISTS users_{guild_id}(
                    id INTEGER PRIMARY KEY,
                    xp INTEGER,
                    level INTEGER,
                    last_message_time FLOAT,
                    spam_count INTEGER,
                    warnings TEXT,
                    message_count INTEGER,
                    last_warn_time FLOAT,
                    emoji_count INTEGER,
                    name_changes INTEGER,
                    last_showcase_post FLOAT
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

    async def set_server_role(self, guild_id, button_name, role_name, role_id, emoji):
        try:
            await self.c.execute(f"""
                INSERT OR REPLACE INTO serverroles_{guild_id}(button_name, role_name, role_id, emoji)
                VALUES (?, ?, ?, ?)
            """, (button_name, role_name, role_id, emoji))
            await self.conn.commit()
        except Exception as e:
            print(f"Error setting server role: {e}")

    async def get_all_faqs(self, guild_id):
        await self.c.execute(f"SELECT number, content FROM faqs_{guild_id}")
        data = await self.c.fetchall()
        return data
    
    async def get_server_role(self, guild_id, button_name):
        await self.c.execute(f"SELECT role_id, emoji FROM serverroles_{guild_id} WHERE button_name = ?", (button_name,))
        data = await self.c.fetchone()
        
        if data:
            return {'role_id': data[0], 'emoji': data[1]}
        return None

    async def set_channel_mapping(self, guild_id, channel_display_name, channel_name, channel_id, message):
        try:
            await self.c.execute(f"""
                INSERT OR REPLACE INTO channelmapping_{guild_id}(channel_display_name, channel_name, channel_id, message)
                VALUES (?, ?, ?, ?)
            """, (channel_display_name, channel_name, channel_id, message))
            await self.conn.commit()
        except Exception as e:
            print(f"Error setting channel mapping: {e}")

    async def get_button_names(self, guild_id):
        await self.c.execute(f"SELECT button_name FROM serverroles_{guild_id}")
        data = await self.c.fetchall()
        return [item[0] for item in data]
    
    async def set_server_channel(self, interaction, guild_id, display_name, channel_name, channel_id):
        try:
            await self.c.execute(f"""
                INSERT OR REPLACE INTO channelmapping_{guild_id}(channel_display_name, channel_name, channel_id)
                VALUES (?, ?, ?)
            """, (display_name, channel_name, channel_id))
            await self.conn.commit()
        except Exception as e:
            print(f"Error setting server channel: {e}")

    async def get_welcome_channel(self, guild_id):
        query = f"SELECT channel_name FROM channelmapping_{guild_id} WHERE message IS NOT NULL LIMIT 1"
        await self.c.execute(query)
        channel_name = await self.c.fetchone()
        return channel_name[0] if channel_name else None
        
    async def get_welcome_message(self, guild_id):
        """
        Retrieve the welcome message associated with a specific guild.
        """
        query = f"SELECT message FROM channelmapping_{guild_id} WHERE message IS NOT NULL LIMIT 1"
        await self.c.execute(query)
        message_row = await self.c.fetchone()
        return message_row[0] if message_row else None
    
    async def add_moderation_log(self, guild_id, action, user_id, moderator_id, reason, timestamp):
        """Add a moderation action to the log."""
        await self.bot.db.c.execute(f"""
            INSERT INTO moderation_logs_{guild_id}(action, user_id, moderator_id, reason, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (action, user_id, moderator_id, reason, timestamp))
        await self.bot.db.conn.commit()

    async def get_showcase_channel(self, guild_id, showcase_display_name="showcase"):
        """
        Retrieve the showcase channel ID associated with a specific guild.
        """
        query = f"SELECT channel_id FROM channelmapping_{guild_id} WHERE channel_display_name = ? LIMIT 1"
        await self.c.execute(query, (showcase_display_name,))
        channel_row = await self.c.fetchone()
        return channel_row[0] if channel_row else None
    
    async def get_support_channel_name(self, guild_id):
        """Retrieve the name of the support channel for a specific guild."""
        await self.c.execute(f"SELECT channel_name FROM channelmapping_{guild_id} WHERE channel_display_name = 'support'")
        data = await self.c.fetchone()
        return data[0] if data else None
    
    async def get_user(self, user_id, guild_id):
        member = self.bot.get_guild(guild_id).get_member(user_id)
        if member is not None and member.bot:
            return None

        await self.c.execute(f"SELECT * FROM users_{guild_id} WHERE id = ?", (user_id,))
        data = await self.c.fetchone()

        if data is None:
            data = (user_id, 0, 0, 0, 0, '[]', 0, None, 0, 0, None)
            await self.c.execute(f"INSERT INTO users_{guild_id} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
            await self.conn.commit()

        user = {
            'id': data[0],
            'xp': data[1],
            'level': data[2],
            'last_message_time': data[3],
            'spam_count': data[4],
            'warnings': data[5],
            'message_count': data[6],
            'last_warn_time': data[7],
            'emoji_count': data[8],
            'name_changes': data[9],
            'last_showcase_post': data[10]
        }
        return user

    async def update_user(self, user, guild_id):
        await self.c.execute(f'''UPDATE users_{guild_id} SET xp = ?, level = ?, 
                    last_message_time = ?, spam_count = ?, warnings = ?, 
                    message_count = ?, last_warn_time = ?, emoji_count = ?, name_changes = ? WHERE id = ?''', 
                    (user['xp'], user['level'], user['last_message_time'], user['spam_count'], 
                        user['warnings'], user['message_count'], user['last_warn_time'], 
                        user['emoji_count'], user['name_changes'], user['id']))
        await self.conn.commit()

    async def get_top_users(self, guild_id, limit):
        await self.c.execute(f"SELECT * FROM users_{guild_id} ORDER BY xp DESC LIMIT ?", (limit * 2,))
        data = await self.c.fetchall()

        users = []
        for user_data in data:
            user = {
                'id': user_data[0],
                'xp': user_data[1],
                'level': user_data[2],
                'last_message_time': user_data[3],
                'spam_count': user_data[4],
                'warnings': user_data[5],
                'message_count': user_data[6],
                'last_warn_time': user_data[7],
                'emoji_count': user_data[8],
                'name_changes': user_data[9],
                'last_showcase_post': user_data[10]
            }
            users.append(user)

        guild = self.bot.get_guild(guild_id)
        valid_users = []
        for user in users:
            try:
                member = await guild.fetch_member(user['id'])
                valid_users.append(user)
                if len(valid_users) == limit:
                    break
            except discord.NotFound:
                continue

        return valid_users

    async def get_rank(self, user_id, guild_id):
        await self.c.execute(f"SELECT id FROM users_{guild_id} ORDER BY xp DESC")
        users = await self.c.fetchall()

        for i, user in enumerate(users, start=1):
            if user[0] == user_id:
                return i
        return None
    
    async def get_bot_channel(self, guild_id):
        """
        Set the bot_channel based on channels in the database.
        Prioritize channels with 'bot' in their name. If none found, use the default channel.
        """
        try:
            # Query the database to find a channel with 'bot' in the name
            await self.c.execute(f"SELECT channel_id FROM channelmapping_{guild_id} WHERE channel_name LIKE '%bot%' LIMIT 1")
            channel_id = await self.c.fetchone()

            if channel_id:  # If a bot channel is found in the database
                self.bot_channel = self.bot.get_channel(channel_id[0])
            else:  # If not, use the default channel
                guild = self.bot.get_guild(guild_id)
                self.bot_channel = guild.default_channel

        except Exception as e:
            print(f"Error in set_bot_channel: {e}")


    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.setup_database(guild.id)

async def setup(bot):
    await bot.add_cog(Database(bot))
