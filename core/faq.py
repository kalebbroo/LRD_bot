import discord
from discord.ext import commands

class FAQ(commands.Cog):
    """A cog for handling FAQs."""

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.get_cog("Database")

    @commands.command(name="faq", help="Retrieve a specific FAQ by number.")
    async def faq_command(self, ctx, faq_number: int = None):
        """
        Handles the !faq command. If a number is provided, it fetches the corresponding FAQ from the database.
        If no number is provided, it instructs the user to use the /faq slash command.
        """
        if not faq_number:
            await ctx.send("Please use the slash command `/faq` to read the FAQs.")
            return

        faq_content = await self.db.get_faq(faq_number, ctx.guild.id)

        if faq_content:
            embed = discord.Embed(title=f"FAQ #{faq_number}", description=faq_content, color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Sorry, I couldn't find FAQ #{faq_number}.")

    @faq_command.error
    async def faq_error(self, ctx, error):
        """Handles errors for the faq_command."""
        if isinstance(error, commands.BadArgument):
            await ctx.send("Invalid FAQ number. Please provide a valid number.")
        else:
            await ctx.send("An unexpected error occurred. Please try again later.")

async def setup(bot):
    await bot.add_cog(FAQ(bot))