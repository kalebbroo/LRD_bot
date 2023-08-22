import discord
from discord.ext import commands
from datetime import datetime, timedelta

class Showcase(commands.Cog):
    def __init__(self, bot, db_cog):
        self.bot = bot
        self.db = db_cog

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Assuming the function get_showcase_channel in Database cog returns the ID of the showcase channel for the guild
        showcase_channel_id = await self.db.get_showcase_channel(message.guild.id)

        if not showcase_channel_id or message.channel.id != showcase_channel_id:
            return

        last_post_time = await self.db.get_last_post_time(message.author.id, message.guild.id)

        # Check if they posted within the last 24 hours
        if last_post_time and datetime.utcnow() - last_post_time < timedelta(days=1):
            await message.delete()
            await message.author.send("You can only post once every 24 hours in the showcase channel.")
            return

        # Update their timestamp in the database
        await self.db.update_last_post_time(message.author.id, message.guild.id, datetime.utcnow())

        # Create a thread (forum) under the post for discussions
        await message.start_thread(name=f"Discussion for {message.author.name}'s post")

    @commands.Cog.listener()
    async def on_thread_join(self, thread):
        showcase_channel_id = await self.db.get_showcase_channel(thread.guild.id)
        if thread.parent_id == showcase_channel_id:
            # If the thread is related to the showcase channel, remove the user's ability to send messages in the parent channel
            await thread.parent.set_permissions(thread.guild.default_role, send_messages=False)
        else:
            await thread.parent.set_permissions(thread.guild.default_role, send_messages=True)

def setup(bot, db_cog):
    bot.add_cog(Showcase(bot, db_cog))
