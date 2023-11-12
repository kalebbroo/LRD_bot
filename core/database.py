import discord
from discord.ext import commands
from dotenv import load_dotenv
import aiosqlite
import datetime
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
                    name TEXT,
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
                    message TEXT,
                    message_id INTEGER
                )
            """)
            # Setup table for showcase
            await self.c.execute(f"""
                CREATE TABLE IF NOT EXISTS showcase_{guild_id}(
                    message_id INTEGER,
                    user_id INTEGER,
                    vote_up INTEGER DEFAULT 0,
                    vote_down INTEGER DEFAULT 0,
                    PRIMARY KEY(message_id, user_id)
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

    # FAQ Methods
    async def handle_faq(self, guild_id, action, number=None, name=None, content=None):
        table_name = f"faqs_{guild_id}"
        try:
            match action:
                case "get":
                    await self.c.execute(f"SELECT name, content FROM {table_name} WHERE number = ?", (number,))
                    row = await self.c.fetchone()
                    return {"name": row[0], "content": row[1]} if row else None
                
                case "add":
                    await self.c.execute(f"INSERT INTO {table_name}(number, name, content) VALUES (?, ?, ?)", (number, name, content))

                case "remove":
                    await self.c.execute(f"DELETE FROM {table_name} WHERE number = ?", (number,))

                case "get_all":
                    await self.c.execute(f"SELECT number, name, content FROM {table_name}")
                    return await self.c.fetchall()
                
                case _:
                    print("Something went wrong in handle_faq call.")
                    return None
                
            await self.conn.commit()
        except Exception as e:
            print(f"Error in handle_faq: {e}")
    
    # Channel Methods
    async def handle_channel(self, guild_id, action, display_name=None, channel_name=None, channel_id=None, message=None, message_id=None):
        table_name = f"channelmapping_{guild_id}"
        try:
            match action:
                case "set_mapping":
                    await self.c.execute(f"INSERT OR REPLACE INTO {table_name}(channel_display_name, channel_name, channel_id, message, message_id) VALUES (?, ?, ?, ?, ?)", 
                                         (display_name, channel_name, channel_id, message, message_id))
                    
                case "get_channel":
                    # Dynamically build query based on provided parameters
                    conditions = []
                    params = []
                    if display_name:
                        conditions.append("LOWER(channel_display_name) = LOWER(?)")
                        params.append(display_name)
                    if channel_name:
                        conditions.append("LOWER(channel_name) = LOWER(?)")
                        params.append(channel_name)
                    if channel_id:
                        conditions.append("channel_id = ?")
                        params.append(channel_id)
                    if message:
                        conditions.append("message = ?")
                        params.append(message)
                    if message_id:
                        conditions.append("message_id = ?")
                        params.append(message_id)

                    query = f"SELECT * FROM {table_name}"
                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)
                    await self.c.execute(query, tuple(params))
                    return await self.c.fetchall()

                case "get_welcome_channel":
                    await self.c.execute(f"SELECT channel_name FROM {table_name} WHERE message IS NOT NULL LIMIT 1")
                    result = await self.c.fetchone()
                    return result[0] if result else None
                
                case "get_support_channel":
                    await self.c.execute(f"SELECT channel_name FROM {table_name} WHERE LOWER(channel_display_name) = 'support'")
                    result = await self.c.fetchone()
                    return result[0] if result else None
                
                case "get_display_names":
                    await self.c.execute(f"SELECT channel_display_name FROM {table_name}")
                    return [item[0] for item in await self.c.fetchall()]
                
                case "get_channel_info":
                    await self.c.execute(f"SELECT channel_display_name, channel_id FROM {table_name}")
                    return [(item[0], item[1]) for item in await self.c.fetchall()]
                
                case "update_channel_message":
                    await self.c.execute(f"UPDATE {table_name} SET message = ? WHERE channel_display_name = ?", (message, display_name))

                case "get_message_id":
                    await self.c.execute(f"SELECT message_id FROM {table_name} WHERE channel_display_name = ?", (display_name,))
                    result = await self.c.fetchone()
                    return result[0] if result else None
                
                case "set_bot_channel":
                    await self.c.execute(f"INSERT OR REPLACE INTO {table_name}(channel_display_name, channel_id) VALUES (?, ?)", ("bot_channel", channel_id))
                
                case "get_bot_channel":
                    await self.c.execute(f"SELECT channel_id FROM {table_name} WHERE channel_display_name = 'bot_channel'")
                    result = await self.c.fetchone()
                    return result[0] if result else None
                
                case "get_showcase_channel":
                    await self.c.execute(f"SELECT * FROM {table_name} WHERE LOWER(channel_display_name) = 'showcase'")
                    result = await self.c.fetchone()
                    if result:
                        print(f"Raw result from the database: {result}")
                        # If you know the exact number of columns, you can unpack them directly:
                        # channel_display_name, channel_name, channel_id, message, message_id = result
                        return result[2]  # Assuming the third column is channel_id
                    else:
                        print("No showcase channel found.")
                        return None
                    
                case "get_admin_channel":
                    await self.c.execute(f"SELECT channel_id FROM {table_name} WHERE LOWER(channel_display_name) = 'admin channel'")
                    result = await self.c.fetchone()
                    if result:
                        print(f"Admin Channel ID found: {result[0]}")
                        return result[0]
                    else:
                        print("No admin channel found.")
                        return None
                                
                case _:
                    print("Something went wrong in handle_channel call.")
                    return None

            await self.conn.commit()
        except Exception as e:
            print(f"Error in handle_channel: {e}")
    
    # Server Role Methods
    async def handle_server_role(self, guild_id, action, button_name=None, role_name=None, role_id=None, emoji=None):
        table_name = f"serverroles_{guild_id}"
        try:
            match action:
                case "set":
                    await self.c.execute(f"INSERT OR REPLACE INTO {table_name}(button_name, role_name, role_id, emoji) VALUES (?, ?, ?, ?)", 
                                        (button_name, role_name, role_id, emoji))

                case "get":
                    await self.c.execute(f"SELECT role_id, emoji FROM {table_name} WHERE LOWER(button_name) = ?", (button_name.lower(),))
                    return await self.c.fetchone()
                
                case "get_all_button_names":
                    await self.c.execute(f"SELECT button_name FROM {table_name}")
                    return [row[0] for row in await self.c.fetchall()]
                
                case _:
                    print("Something went wrong in handle_server_role call.")
                    return None
            
            await self.conn.commit()
        except Exception as e:
            print(f"Error in handle_server_role: {e}")
    
    # Showcase Methods
    async def handle_showcase(self, guild_id, action, user_id=None, timestamp=None, message_id=None, vote_type=None):
        table_name = f"showcase_{guild_id}"
        try:
            match action:
                case "get_last_post_time":
                    await self.c.execute(f"SELECT last_post_time FROM {table_name} WHERE user_id = ?", (user_id,))
                    data = await self.c.fetchone()
                    return datetime.datetime.utcfromtimestamp(data[0]) if data else None
                
                case "update_last_post_time":
                    await self.c.execute(f"INSERT OR REPLACE INTO {table_name}(user_id, last_post_time) VALUES (?, ?)", (user_id, timestamp.timestamp()))

                case "add_vote":
                    # Check if a record already exists for this user's vote on this message
                    await self.c.execute(f"SELECT 1 FROM {table_name} WHERE message_id = ? AND user_id = ?", (message_id, user_id))
                    exists = await self.c.fetchone()

                    # If a record exists, update the vote
                    if exists:
                        await self.c.execute(f"UPDATE {table_name} SET vote_up = ?, vote_down = ? WHERE message_id = ? AND user_id = ?",
                                            (1 if vote_type == "vote_up" else 0, 1 if vote_type == "vote_down" else 0, message_id, user_id))
                    else:
                        # If no record exists, insert a new one with the vote
                        await self.c.execute(f"INSERT INTO {table_name} (message_id, user_id, vote_up, vote_down) VALUES (?, ?, ?, ?)",
                                            (message_id, user_id, 1 if vote_type == "vote_up" else 0, 1 if vote_type == "vote_down" else 0))
                    return True  # Return True as the operation is successful

                case "get_vote_count":
                    await self.c.execute(f"SELECT COUNT(*) FROM {table_name} WHERE message_id = ? AND {vote_type} = 1", (message_id,))
                    result = await self.c.fetchone()
                    return result[0] if result else 0
                
                case "is_leading_post":
                    await self.c.execute(f"SELECT message_id, COUNT(*) as vote_count FROM {table_name} WHERE vote_up = 1 GROUP BY message_id ORDER BY vote_count DESC LIMIT 1")
                    data = await self.c.fetchone()
                    return data[0] == message_id if data else False
                
                case "get_vote_status":
                    # Fetch the current vote status for a given user and message
                    await self.c.execute(f"SELECT vote_up, vote_down FROM {table_name} WHERE user_id = ? AND message_id = ?", (user_id, message_id))
                    data = await self.c.fetchone()
                    return data  # This will return a tuple (vote_up, vote_down) or None

                case "change_vote":
                    # Update the vote status for a given user and message
                    if vote_type == "vote_up":
                        await self.c.execute(f"UPDATE {table_name} SET vote_up = 1, vote_down = 0 WHERE user_id = ? AND message_id = ?", (user_id, message_id))
                    elif vote_type == "vote_down":
                        await self.c.execute(f"UPDATE {table_name} SET vote_up = 0, vote_down = 1 WHERE user_id = ? AND message_id = ?", (user_id, message_id))
                    return True  # Indicate the operation was successful
                    
                case "get_all_message_ids":
                    await self.c.execute(f"SELECT DISTINCT message_id FROM {table_name}")
                    return [item[0] for item in await self.c.fetchall()]
                
                case "save_new_showcase":
                    await self.c.execute(f"INSERT INTO {table_name}(user_id, message_id, vote_up, vote_down) VALUES (?, ?, 0, 0)", (user_id, message_id))

                case "remove_message":
                    await self.c.execute(f"DELETE FROM {table_name} WHERE message_id = ?", (message_id,))
                    print(f"Removed message {message_id} from showcase table.")
                
                case _:
                    print("Something went wrong in handle_showcase call.")
                    return None
                
            await self.conn.commit()
        except Exception as e:
            print(f"Error in handle_showcase: {e}")
    
    # User Methods
    async def handle_user(self, guild_id, action, user_id=None, user_data=None, limit=None):
        table_name = f"users_{guild_id}"
        try:
            match action:
                case "get":
                    await self.c.execute(f"SELECT * FROM {table_name} WHERE id = ?", (user_id,))
                    data = await self.c.fetchone()
                    if data is None:
                        # Initialize with default data if not present
                        data = (user_id, 0, 0, 0, 0, '[]', 0, None, 0, 0, None)
                        await self.c.execute(f"INSERT OR IGNORE INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
                    return {
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
                case "update":
                    await self.c.execute(f'''UPDATE {table_name} SET xp = ?, level = ?, 
                                last_message_time = ?, spam_count = ?, warnings = ?, 
                                message_count = ?, last_warn_time = ?, emoji_count = ?, 
                                name_changes = ? WHERE id = ?''', 
                                (user_data['xp'], user_data['level'], user_data['last_message_time'], 
                                user_data['spam_count'], user_data['warnings'], user_data['message_count'], 
                                user_data['last_warn_time'], user_data['emoji_count'], user_data['name_changes'], 
                                user_data['id']))
                    
                case "get_top_users":
                    await self.c.execute(f"SELECT * FROM {table_name} ORDER BY xp DESC LIMIT ?", (limit * 2,))
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
                
                case "get_rank":
                    await self.c.execute(f"SELECT id FROM {table_name} ORDER BY xp DESC")
                    users = await self.c.fetchall()
                    for i, user in enumerate(users, start=1):
                        if user[0] == user_id:
                            return i
                        
                case _:
                    print("Something went wrong in handle_user call.")
                    return None
                
            await self.conn.commit()
        except Exception as e:
            print(f"Error in handle_user: {e}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.setup_database(guild.id)

async def setup(bot):
    await bot.add_cog(Database(bot))