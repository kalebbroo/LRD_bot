import discord
from discord.ext import commands

class AdminCommands(commands.Cog):
    """A cog for handling FAQs."""

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.get_cog("Database")
        self.embed_cog = bot.get_cog("CreateEmbed")

    @commands.command(name="faq", help="Retrieve a specific FAQ by number.")
    async def faq_command(self, ctx, faq_number: int = None):
        """
        Handles the !faq command. If a number is provided, it fetches the corresponding FAQ from the database.
        If no number is provided, it instructs the user to use the /faq slash command.
        """
        if not faq_number:
            embed_data = {
                "title": "FAQ Command",
                "description": "Please use the slash command `/faq` to read the FAQs.",
                "color": discord.Color.blue()
            }
            embed = await self.embed_cog.create_embed(**embed_data)
            await ctx.send(embed=embed)
            return

        faq_content = await self.db.get_faq(faq_number, ctx.guild.id)

        if faq_content:
            embed_data = {
                "title": f"FAQ #{faq_number}",
                "description": faq_content,
                "color": discord.Color.blue()
            }
            embed = await self.embed_cog.create_embed(**embed_data)
            await ctx.send(embed=embed)
        else:
            embed_data = {
                "title": "FAQ Not Found",
                "description": f"Sorry, I couldn't find FAQ #{faq_number}.",
                "color": discord.Color.red()
            }
            embed = await self.embed_cog.create_embed(**embed_data)
            await ctx.send(embed=embed)

    @faq_command.error
    async def faq_error(self, ctx, error):
        """Handles errors for the faq_command."""
        if isinstance(error, commands.BadArgument):
            embed_data = {
                "title": "Invalid Argument",
                "description": "Invalid FAQ number. Please provide a valid number.",
                "color": discord.Color.red()
            }
            embed = await self.embed_cog.create_embed(**embed_data)
            await ctx.send(embed=embed)
        else:
            embed_data = {
                "title": "Error",
                "description": "An unexpected error occurred. Please try again later.",
                "color": discord.Color.red()
            }
            embed = await self.embed_cog.create_embed(**embed_data)
            await ctx.send(embed=embed)

    @commands.command(name="howtoinstall", help="Directs the user to the #howtoinstall channel.")
    async def howtoinstall_command(self, ctx):
        """Informs the user to check the #howtoinstall channel."""
        
        embed_data = {
            "title": "Installation Instructions",
            "description": "Please check the `#howtoinstall` channel for detailed installation instructions.",
            "color": discord.Color.green()
        }
        
        embed = await self.embed_cog.create_embed(**embed_data)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))