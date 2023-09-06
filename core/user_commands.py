import discord
from discord.ext import commands
from discord import app_commands, Embed, Colour
from discord.app_commands import Choice

class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.get_cog("Database")
        self.embed_cog = bot.get_cog("CreateEmbed")

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
    @app_commands.choices(command_name=[
        Choice(name='Overview', value="overview"),
        Choice(name='FAQ', value="faq"),
        Choice(name='Showcase Server', value="showcase_server"),
        Choice(name='Setup', value="setup"),
        Choice(name='Mute', value="mute"),
        Choice(name='Unmute', value="unmute"),
        Choice(name='Kick', value="kick"),
        Choice(name='Ban', value="ban"),
        Choice(name='Adjust Roles', value="adjust_roles"),
        Choice(name='Announcement', value="announcement"),
        Choice(name='Mute Listener', value="mute_listener"),
        Choice(name='on_message Listener', value="on_message_listener")
    ])
    async def help(self, interaction, command_name: str):
        await interaction.response.defer()
        try:
            title = "Help"
            description = "Overview of commands"
            fields = []

            match command_name:
                case "overview":
                    fields = [
                        ("`/help`", "Displays detailed help for specified commands. Use `/help <command_name>` to see details. A list of commands will be displayed."),
                        ("`/faq`", "Displays a list of frequently asked questions. Use `/faq <number>` to see a specific FAQ. A list of FAQs will be displayed.")
                        # ... other commands ...
                    ]
                case "faq":
                    title = "FAQ Command"
                    description = "Use `/faq <number>` to retrieve the FAQ of a specified number. If no number is provided, a list of FAQs will be displayed. Then, choose the FAQ you want to read more about."
                case "showcase_server":
                    title = "Showcase Server Command"
                    description = "This command explains the showcase server functionality. It is mainly informative and is provided for understanding how showcase servers work."
                case "setup":
                    title = "Setup Command"
                    description = (
                        "The `/setup` command initiates the setup process for various bot functionalities. Here's a detailed breakdown of the sub-commands:\n"
                        "\n**Add FAQ:** This allows you to add a new FAQ entry. A modal will appear for you to input the FAQ details. Once submitted, the FAQ will be stored.\n"
                        "\n**Remove FAQ:** Removes an existing FAQ. After selecting, you'll see a list of all FAQs. Choose one to remove it.\n"
                        "\n**Map Roles and Create Buttons:** Lets you map server roles to button display names and emojis. A modal will guide you through the mapping process.\n"
                        "\n**Map Channel Names to Database:** Links specific channel names and IDs in the database. A modal will guide you through the mapping.\n"
                        "\n**Welcome Page Setup:** Used to set up the welcome page for new users. The system will guide you through the configuration process."
                    )
                case "mute":
                    title = "Mute Command"
                    description = "Use `/mute @member reason` to mute a specific member. The member will not be able to send messages or speak in voice channels. A confirmation message will appear if the mute is successful."
                case "unmute":
                    title = "Unmute Command"
                    description = "Use `/unmute @member` to unmute a specific member. The member will regain their messaging and speaking permissions. A confirmation message will appear if the unmute is successful."
                case "kick":
                    title = "Kick Command"
                    description = "Use `/kick @member reason` to kick a member out of the server. The member can rejoin unless they're banned. A confirmation message will appear if the kick is successful."
                case "ban":
                    title = "Ban Command"
                    description = "Use `/ban @member reason` to permanently ban a member from the server. They can't rejoin unless unbanned. A confirmation message will appear if the ban is successful."
                case "adjust_roles":
                    title = "Adjust Roles Command"
                    description = "Use `/adjust_roles @user add|remove` to add or remove roles from a user. An interactive menu will appear for you to select the role. A confirmation message will appear once the role has been adjusted."
                case "announcement":
                    title = "Announcement Command"
                    description = "Use `/announcement title description #channel footer image_url` to send an announcement to a specified channel, tagging @everyone. A preview of the announcement will be shown before it's sent."
                case "mute_listener":
                    title = "Mute Listener"
                    description = "This is a passive listener. When a new channel is created, it ensures that members with the 'Muted' role cannot speak or send messages in it. There is no need to activate this, it runs automatically."
                case "on_message_listener":
                    title = "on_message Listener"
                    description = "This is a passive listener. When a new member uses certain keywords in non-support channels, it will guide them to the support channel. This listener runs automatically and requires no user interaction."

            # Create the embed using the embed cog
            embed = await self.embed_cog.create_embed(
                title=title,
                description=description,
                color=Colour.blue(),
                fields=[(*field, False) for field in fields]
            )
            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error in help command: {e}")
            error_embed = await self.embed_cog.create_embed(
                title="Error",
                description="An error occurred while processing your request.",
                color=Colour.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)


    @commands.Cog.listener()
    async def on_application_command_error(self, interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("You do not have the necessary permissions to run this command.", ephemeral=True)
        # You can add other error checks here as well
        else:
            await interaction.response.send_message("An error occurred while processing the command.", ephemeral=True)
            # Optionally log the error for debugging purposes
            print(f"Error in command {interaction.command}: {error}")



async def setup(bot):
    await bot.add_cog(UserCommands(bot))