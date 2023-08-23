from discord.ext import commands
from discord.utils import get
import discord
from discord.app_commands import Choice

class AdminControls(commands.Cog):
    def __init__(self, bot, db_cog):
        self.bot = bot
        self.db = db_cog

    @commands.app_commands.command(name='setup', description='Admin setup for various functionalities.')
    @commands.app_commands.describe(choice="The setup action you want to perform.")
    @commands.app_commands.choices(choice=[
        Choice(name='Add FAQ', value="addFAQ"),
        Choice(name='Remove FAQ', value="removeFAQ"),
        Choice(name='Set Role', value="setRole"),
        Choice(name='Set Channel', value="setChannel")
    ])
    async def setup(self, interaction, choice: str, *args):
        if choice == "addFAQ":
            number = int(args[0])
            content = args[1]
            try:
                await self.db.add_faq(number, content, interaction.guild.id)
                await interaction.send(f"FAQ #{number} has been added successfully.")
            except Exception as e:
                await interaction.send(f"Error adding FAQ: {e}")

        elif choice == "removeFAQ":
            number = int(args[0])
            try:
                await self.db.remove_faq(number, interaction.guild.id)
                await interaction.send(f"FAQ #{number} has been removed successfully.")
            except Exception as e:
                await interaction.send(f"Error removing FAQ: {e}")

        elif choice == "setRole":
            # Display role names defined in the database for the server
            role_names = ["Read the Rules", "Patreon Announcements", "Announcements", "Behind the Scenes", "Showcase"]
            selected_role_name = await interaction.context_menu(
                options=[discord.SelectOption(label=name) for name in role_names],
                placeholder="Select a predefined role name"
            )

            # Display all roles from the server to the admin
            server_roles = interaction.guild.roles
            server_role_names = [role.name for role in server_roles]
            selected_server_role = await interaction.context_menu(
                options=[discord.SelectOption(label=name) for name in server_role_names],
                placeholder="Select a server role"
            )

            role = discord.utils.get(server_roles, name=selected_server_role.value)
            if role:
                # Save the role name and ID to the database
                await self.db.set_server_role(interaction.guild.id, selected_role_name.value, role.id)
                await interaction.send(f"Role {selected_role_name.value} linked to {role.name}.")
            else:
                await interaction.send(f"Error: Role not found.")

        elif choice == "setChannel":
            channel_type = args[0]
            channel_id = int(args[1])
            channel = self.bot.get_channel(channel_id)
            if not channel:
                await interaction.send(f"Channel with ID {channel_id} not found.")
                return
            
            if channel_type == "showcase":
                await self.db.set_showcase_channel(interaction.guild.id, channel_id)
                await interaction.send(f"Channel {channel.mention} set as the showcase channel.")
            else:
                await interaction.send(f"Channel {channel.mention} set for {channel_type} functionality.")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message is from a bot
        if message.author.bot:
            return

        # Check if the message is in the support channel (replace 'support' with your actual support channel's name)
        if message.channel.name == 'support':
            return

        # Check for keywords
        keywords = ["help", "support", "assist"]
        if any(keyword in message.content.lower() for keyword in keywords):
            await message.reply(f"If you are looking for help or support, please go to the #support channel.")


def setup(bot, db_cog):
    bot.add_cog(AdminControls(bot, db_cog))
