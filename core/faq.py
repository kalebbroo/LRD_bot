import discord
from discord.ext import commands
import re

class FAQ(commands.Cog):
    def __init__(self, bot:commands.Bot, db_cog):
        self.bot = bot
        self.db = db_cog

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Check if the message matches the pattern "FAQ #<number>"
        match = re.search(r"FAQ #(\d+)", message.content)
        if not match:
            return

        # Extract the FAQ number from the message
        faq_number = int(match.group(1))
        
        # Fetch the FAQ content from the database
        faq_content = await self.db.get_faq(faq_number, message.guild.id)

        if faq_content:
            # Reply with the FAQ content
            await message.reply(f"{message.author.mention} Here's the FAQ #{faq_number}:\n\n{faq_content}")
        else:
            await message.reply(f"{message.author.mention} Sorry, I couldn't find FAQ #{faq_number}.")

def setup(bot:commands.Bot, db_cog):
    bot.add_cog(FAQ(bot, db_cog))
