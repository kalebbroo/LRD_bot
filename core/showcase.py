import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime, timedelta
import aiosqlite

class VoteButton(Button):
    def __init__(self, showcase_cog, label, emoji, post_id):
        super().__init__(style=discord.ButtonStyle.primary, label=label, emoji=emoji, custom_id=f"vote_{post_id}")
        self.post_id = post_id
        self.showcase_cog = showcase_cog

    async def callback(self, interaction):
        # Handle vote using the Showcase cog's method
        await self.showcase_cog.add_vote(self.post_id, interaction.user.id)
        await interaction.response.send_message(f"Thanks for your vote!", ephemeral=True)

class Showcase(commands.Cog):
    def __init__(self, bot, db_cog):
        self.bot = bot
        self.db = db_cog

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        showcase_channel_id = await self.db.get_showcase_channel(message.guild.id)

        if not showcase_channel_id or message.channel.id != showcase_channel_id:
            return

        if not message.attachments or not message.content:
            await message.delete()
            await message.author.send("Your showcase post must include media and a description.")
            return

        last_post_time = await self.db.get_last_post_time(message.author.id, message.guild.id)

        if last_post_time and datetime.utcnow() - last_post_time < timedelta(days=1):
            await message.delete()
            await message.author.send("You can only post once every 24 hours in the showcase channel.")
            return

        embed = discord.Embed(description=message.content)
        embed.set_image(url=message.attachments[0].url)
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)

        view = View()
        # Pass the Showcase cog reference to the VoteButton
        view.add_item(VoteButton(self, "Vote Up", "👍", message.id))
        view.add_item(VoteButton(self, "Vote Down", "👎", message.id))

        # Post the embed
        await message.channel.send(embed=embed, view=view)
        # Delete the original message
        await message.delete()

        await self.db.update_last_post_time(message.author.id, message.guild.id, datetime.utcnow())
        await message.start_thread(name=f"Discussion for {message.author.name}'s post")

    # Function to record a vote for a post
    async def add_vote(self, post_id, user_id):
        try:
            await self.c.execute(f"INSERT INTO votes(post_id, user_id) VALUES (?, ?)", (post_id, user_id))
            await self.conn.commit()
        except aiosqlite.IntegrityError:
            # This error will be raised if a vote by this user for this post already exists
            # (due to the primary key constraint)
            pass

    # Function to get the number of votes for a post
    async def get_votes(self, post_id):
        await self.c.execute(f"SELECT COUNT(*) FROM votes WHERE post_id = ?", (post_id,))
        data = await self.c.fetchone()
        return data[0] if data else 0

def setup(bot, db_cog):
    bot.add_cog(Showcase(bot, db_cog))
