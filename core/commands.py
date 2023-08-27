import discord
from discord.ext import commands
from discord import app_commands, Embed, Colour

class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.get_cog("Database")

    @app_commands.command(name='faq', description='Display all FAQs.')
    async def display_faqs(self, interaction):
        await interaction.response.defer()
        # Retrieve all FAQs from the database
        faqs = await self.db.get_all_faqs(interaction.guild.id)
        
        if not faqs:
            await interaction.followup.send("No FAQs have been set up yet.")
            return

        # Construct the FAQ display
        embed = discord.Embed(title="Frequently Asked Questions", description="")
        for number, content in faqs:
            embed.add_field(name=f"FAQ #{number}", value=content, inline=False)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='help', description='Displays help information.')
    async def help(self, interaction):
        await interaction.response.defer()
        try:
            user_help = """
            **User Commands**:
            - `/help`: Displays this help message.
            - explain showcase server
            - `/faq`: Displays a list of FAQs.

            """

            admin_help = """
            **Admin Commands**:
        - `/setup` command to manage various bot functionalities. Upon invoking the command, you'll have the option to choose from:

        - **Add FAQ**: Define a new FAQ entry.
            - Provide a unique number for the FAQ and its content.
            - The bot will confirm once the FAQ is added. Any errors will be communicated.
        
        - **Remove FAQ**: Delete an existing FAQ entry.
            - Provide the number associated with the FAQ you wish to remove.
            - You'll receive a confirmation upon successful removal or an error message if something goes wrong.
            
        - **Set Role**: Link predefined roles to actual roles in your server.
            - Initially, select a role name from a predefined list (like "Read the Rules").
            - Next, match it to an actual role from your server.
            - The bot will link these and confirm or notify you if the role isn't found.
        
        - **Set Channel**: Assign a specific channel for a bot function.
            - Specify the function (e.g., "showcase") and the desired channel's ID.
            - For a "showcase" type, the bot sets the channel for showcasing. For other types, it confirms the channel's assignment for the chosen function.
            - Errors, like invalid channel IDs, will be communicated.




            """
            # Check if the user is an admin
            if interaction.user.guild_permissions.administrator:
                await interaction.followup.send(f"{user_help}\n{admin_help}")
                print("Admin used /help")
            else:
                await interaction.followup.send(user_help)
                print("User used /help")
        except Exception as e:
            print(f"Error in help command: {e}")
            await interaction.followup.send("Error in help command.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(UserCommands(bot))