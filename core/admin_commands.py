import discord
from discord.ext import commands

class AdminCommands(commands.Cog):
    """A cog for handling inline commands."""

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
        #print(f"FAQ number from command: {faq_number}")  # Debugging
        if not faq_number:
            embed_data = {
                "title": "FAQ Command",
                "description": "Please use the slash command `/faq` to read the FAQs.",
                "color": discord.Color.blue()
            }
            embed = await self.embed_cog.create_embed(**embed_data)
            await ctx.send(embed=embed)
            return

        faq_data = await self.db.get_faq(faq_number, ctx.guild.id)

        if faq_data:
            embed_data = {
                "title": f"FAQ #{faq_number} - {faq_data['name']}",
                "description": faq_data['content'],
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

    @commands.command(name="go_read", help="Removes the I can Read role from the user.")
    @commands.has_permissions(administrator=True)
    async def go_read_command(self, ctx):
        """Removes the I can Read role from the user.
            This will make the read the rules again.
            All channel access will be removed"""
        role = discord.utils.get(ctx.guild.roles, name="I can Read")
        await ctx.author.remove_roles(role)
        
        embed_data = {
            "title": "Please Read the Rules Again",
            "description": "The I can Read role has been removed from you. " \
                        "An admin has requested that you read the rules again. " \
                        "Please read the rules again to get the I can Read role back. " \
                        "You will not be able to access any channels until you do so.",
            "color": discord.Color.green()
        }
        embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)
        await ctx.author.send(embed=embed)  # Sends the embed to the user's DM

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))