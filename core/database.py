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
                    vote_up TEXT,
                    vote_down TEXT,
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

    async def get_faq(self, number, guild_id):
        try:
            await self.c.execute(f"SELECT name, content FROM faqs_{guild_id} WHERE number = ?", (number,))
            row = await self.c.fetchone()
            
            if row:
                return {"name": row[0], "content": row[1]}
            return None
        except Exception as e:
            print(f"Error in get_faq: {e}")
            return None

    async def add_faq(self, number, name, content, guild_id):
        try:
            await self.c.execute(f"INSERT INTO faqs_{guild_id}(number, name, content) VALUES (?, ?, ?)", (number, name, content))
            await self.conn.commit()
        except Exception as e:
            print(f"Error in add_faq: {e}")

    async def remove_faq(self, number, guild_id):
        try:
            await self.c.execute(f"DELETE FROM faqs_{guild_id} WHERE number = ?", (number,))
            await self.conn.commit()
        except Exception as e:
            print(f"Error in remove_faq: {e}")

    async def get_all_faqs(self, guild_id):
        try:
            await self.c.execute(f"SELECT number, name, content FROM faqs_{guild_id}")
            return await self.c.fetchall()
        except Exception as e:
            print(f"Error in get_all_faqs: {e}")
            return []

    async def get_last_post_time(self, user_id, guild_id):
        """
        Retrieve the timestamp of the last post time for a user in a specific guild.
        Args:
        - user_id (int): The ID of the user.
        - guild_id (int): The ID of the guild.
        Returns:
        - datetime.datetime | None: The last post time as a datetime object or None if not found.
        """
        try:
            await self.c.execute(f"SELECT last_post_time FROM showcase_{guild_id} WHERE user_id = ?", (user_id,))
            data = await self.c.fetchone()
            if data:
                # Convert the timestamp back to a datetime object
                return datetime.datetime.utcfromtimestamp(data[0])
            return None
        except Exception as e:
            print(f"Error in get_last_post_time: {e}")
            return None


    async def update_last_post_time(self, user_id, guild_id, timestamp):
        """
        Update the last post time for a user in a specific guild.
        Args:
        - user_id (int): The ID of the user.
        - guild_id (int): The ID of the guild.
        - timestamp (datetime.datetime): The timestamp to set as the last post time.
        Returns:
        - None
        """
        try:
            # Convert the datetime object to a string representation of a timestamp
            timestamp = timestamp.timestamp()
            await self.c.execute(f"INSERT OR REPLACE INTO showcase_{guild_id}(user_id, last_post_time) VALUES (?, ?)", (user_id, timestamp))
            await self.conn.commit()
        except Exception as e:
            print(f"Error in update_last_post_time: {e}")


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
    
    async def get_server_role(self, guild_id, button_name):
        try:
            await self.c.execute(f"SELECT role_id, emoji FROM serverroles_{guild_id} WHERE LOWER(button_name) = ?", (button_name.lower(),))
            data = await self.c.fetchone()
            
            if data:
                return {'role_id': data[0], 'emoji': data[1]}
            return None
        except Exception as e:
            print(f"Error in get_server_role: {e}")
            return None

    async def set_channel_mapping(self, guild_id, display_name, channel_name, channel_id, message, message_id):
        try:
            table_name = f"channelmapping_{guild_id}"
            await self.c.execute(f"""
                INSERT OR REPLACE INTO {table_name} (channel_display_name, channel_name, channel_id, message, message_id)
                VALUES (?, ?, ?, ?, ?)
            """, (display_name, channel_name, channel_id, message, message_id))
            await self.conn.commit()
        except Exception as e:
            print(f"Error setting channel mapping: {e}")

    async def get_button_names(self, guild_id):
        try:
            await self.c.execute(f"SELECT button_name FROM serverroles_{guild_id}")
            data = await self.c.fetchall()
            return [item[0] for item in data]
        except Exception as e:
            print(f"Error in get_button_names: {e}")
            return []
    
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
        Retrieve the showcase channel ID by searching the guild channels.
        """
        try:
            guild = self.bot.get_guild(guild_id)
            
            if not guild:
                print(f"Guild with ID {guild_id} not found.")
                return None

            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel) and channel.name.lower() == showcase_display_name.lower():
                    #print(f"Found showcase channel in guild with ID: {channel.id}")
                    return channel.id

            print("No matching showcase channel found in the guild.")
            return None

        except Exception as e:
            print(f"Error in get_showcase_channel: {e}")
            return None
    
    async def get_admin_channel(self, guild_id):
        """
        Get the ID of the first channel from the server that contains the word 'admin' or 'staff' in its name.
        """
        guild = self.bot.get_guild(guild_id)
        if not guild:
            print("Error: Guild not found.")
            return None

        # Look for a channel with 'admin' or 'staff' in its name
        for channel in guild.text_channels:
            if 'admin' in channel.name.lower() or 'staff' in channel.name.lower():
                return channel.id

        # If no matching channel is found
        print("Error finding admin channel.")
        return None
    
    async def get_support_channel_name(self, guild_id):
        try:
            await self.c.execute(f"SELECT channel_name FROM channelmapping_{guild_id} WHERE LOWER(channel_display_name) = 'support'")
            data = await self.c.fetchone()

            if data:
                return data[0]
            return None
        except Exception as e:
            print(f"Error in get_support_channel_name: {e}")
            return None
    
    async def get_user(self, user_id, guild_id):
        member = self.bot.get_guild(guild_id).get_member(user_id)
        if member is not None and member.bot:
            print(f"User {user_id} is a bot.")
            return None

        await self.c.execute(f"SELECT * FROM users_{guild_id} WHERE id = ?", (user_id,))
        data = await self.c.fetchone()

        if data is None:
            data = (user_id, 0, 0, 0, 0, '[]', 0, None, 0, 0, None)
            await self.c.execute(f"INSERT OR IGNORE INTO users_{guild_id} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
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

    async def add_vote(self, guild_id, message_id, user_id, vote_type):
        try:
            table_name = f"showcase_{guild_id}"
            # Check if the user has already voted on this post
            await self.c.execute(f"SELECT vote_up, vote_down FROM {table_name} WHERE message_id = ? AND user_id = ?", (message_id, user_id))
            data = await self.c.fetchone()
            if data:
                vote_up, vote_down = data

                # Check if the user is trying to vote the same way again
                if (vote_type == "vote_up" and vote_up == 1) or (vote_type == "vote_down" and vote_down == 1):
                    return False  # User already voted this way
                # Update the vote, reset the other type of vote to 0
                opposite_vote_type = "vote_down" if vote_type == "vote_up" else "vote_up"
                await self.c.execute(f"UPDATE {table_name} SET {vote_type} = 1, {opposite_vote_type} = 0 WHERE message_id = ? AND user_id = ?", (message_id, user_id))
            else:
                # Insert a new vote
                await self.c.execute(f"INSERT INTO {table_name}(message_id, user_id, vote_up, vote_down) VALUES (?, ?, ?, ?)",
                                    (message_id, user_id, 1 if vote_type == "vote_up" else 0, 1 if vote_type == "vote_down" else 0))
            await self.conn.commit()
            return True  # Indicates the vote was added or updated
        except Exception as e:
            print(f"Error: {e}")
            return False

        
    async def get_vote_count_for_post(self, guild_id, message_id, vote_type):
        table_name = f"showcase_{guild_id}"
        await self.c.execute(f"SELECT COUNT(*) FROM {table_name} WHERE message_id = ? AND {vote_type} = 1", (message_id,))
        data = await self.c.fetchone()
        return data[0] if data else 0

    async def is_leading_post(self, guild_id, message_id):
        table_name = f"showcase_{guild_id}"
        await self.c.execute(f"SELECT message_id, COUNT(*) as vote_count FROM {table_name} WHERE vote_up = 1 GROUP BY message_id ORDER BY vote_count DESC LIMIT 1")
        data = await self.c.fetchone()
        return data[0] == message_id if data else False

    async def get_channel_display_names(self, guild_id):
        try:
            await self.c.execute(f"SELECT channel_display_name FROM channelmapping_{guild_id}")
            data = await self.c.fetchall()
            return [item[0] for item in data]
        except Exception as e:
            print(f"Error in get_channel_display_names: {e}")
            return []
        
    async def get_id_from_display(self, guild_id, display_name):
        # Construct the query
        query = f"""SELECT channel_id FROM channelmapping_{guild_id}
                WHERE channel_display_name = ?"""
        # Execute the query
        await self.c.execute(query, (display_name,))
        result = await self.c.fetchone()
        # Return the result
        if result:
            return result[0]
        else:
            return None
        
    async def get_support_channel(self, guild_id):
        try:
            query = f"""SELECT channel_display_name FROM channelmapping_{guild_id}
                        WHERE channel_display_name = ?"""
            await self.c.execute(query, ("Support",))
            result = await self.c.fetchone()
            if result:
                return result[0]  # This will now return the display name
            else:
                return None
        except Exception as e:
            print(f"Error in get_support_channel: {e}")
            return None

    async def get_support_message(self, guild_id, display_name):
        try:
            query = f"""SELECT message FROM channelmapping_{guild_id}
                        WHERE channel_display_name = ?"""
            print(f"Executing query: {query} with display_name: {display_name}")  # Debugging line
            await self.c.execute(query, (display_name,))
            result = await self.c.fetchone()
            print(f"Query result: {result}")  # Debugging line
            if result:
                return result[0]
            else:
                return None
        except Exception as e:
            print(f"Error in get_support_message: {e}")
            return None
        
    async def update_channel_message(self, guild_id, channel_display_name, message):
        try:
            query = f"""UPDATE channelmapping_{guild_id}
                        SET message = ?
                        WHERE channel_display_name = ?"""
            await self.c.execute(query, (message, channel_display_name))
            await self.conn.commit()
            return True
        except Exception as e:
            print(f"Error in update_channel_message: {e}")
            return False

    async def get_channel_info(self, guild_id):
        try:
            await self.c.execute(f"SELECT channel_display_name, channel_id FROM channelmapping_{guild_id}")
            data = await self.c.fetchall()
            return [(item[0], item[1]) for item in data]  # Return a list of tuples (channel_display_name, channel_id)
        except Exception as e:
            print(f"Error in get_channel_info: {e}")
            return []

    async def get_all_message_ids(self, guild_id):
        try:
            await self.c.execute(f"SELECT DISTINCT message_id FROM showcase_{guild_id}")
            data = await self.c.fetchall()
            return [item[0] for item in data]
        except Exception as e:
            print(f"Error in get_all_message_ids: {e}")
            return []

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.setup_database(guild.id)

async def setup(bot):
    await bot.add_cog(Database(bot))
