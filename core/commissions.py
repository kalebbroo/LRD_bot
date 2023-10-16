import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import Colour
from datetime import datetime, timedelta


class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



async def setup(bot):
    await bot.add_cog(Support(bot))