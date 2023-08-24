from discord.ext import commands
from discord.utils import get
import discord
import datetime
from discord import app_commands, Embed, Colour
from discord.app_commands import Choice

class AdminControls(commands.Cog):
    def __init__(self, bot, db_cog):
        self.bot = bot
        self.db = db_cog

    @app_commands.command(name='setup', description='Admin setup for various functionalities.')
    @app_commands.describe(choice="The setup action you want to perform.")
    @app_commands.choices(choice=[
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
                await self.bot.db.add_faq(number, content, interaction.guild.id)
                await interaction.send(f"FAQ #{number} has been added successfully.")
            except Exception as e:
                await interaction.send(f"Error adding FAQ: {e}")

        elif choice == "removeFAQ":
            number = int(args[0])
            try:
                await self.bot.db.remove_faq(number, interaction.guild.id)
                await interaction.send(f"FAQ #{number} has been removed successfully.")
            except Exception as e:
                await interaction.send(f"Error removing FAQ: {e}")

        elif choice == "setRole":
            # Assuming there's a method in your db cog for these operations
            role_names = await self.bot.db.get_predefined_role_names(interaction.guild.id)
            server_roles = interaction.guild.roles
            server_role_names = [role.name for role in server_roles]
            # NOTE: `interaction.context_menu` is a placeholder. Actual implementation may vary.
            selected_role_name = await interaction.context_menu(
                options=[discord.SelectOption(label=name) for name in role_names],
                placeholder="Select a predefined role name"
            )
            selected_server_role = await interaction.context_menu(
                options=[discord.SelectOption(label=name) for name in server_role_names],
                placeholder="Select a server role"
            )
            role = discord.utils.get(server_roles, name=selected_server_role.value)
            if role:
                await self.bot.db.set_server_role(interaction.guild.id, selected_role_name.value, role.id)
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
                await self.bot.db.set_showcase_channel(interaction.guild.id, channel_id)
                await interaction.send(f"Channel {channel.mention} set as the showcase channel.")
            else:
                await self.bot.db.set_channel_for_functionality(interaction.guild.id, channel_id, channel_type)
                await interaction.send(f"Channel {channel.mention} set for {channel_type} functionality.")

    @app_commands.command(name='mute', description='Mute a member')
    @app_commands.describe(user='The member to mute')
    @app_commands.describe(reason='The reason for the mute')
    @app_commands.checks.has_permissions(administrator=True)
    async def mute(self, interaction, user: discord.Member, reason: str = None):
        await interaction.response.defer()
        try:
            role = get(interaction.guild.roles, name="Muted")
            if not role:
                role = await interaction.guild.create_role(name="Muted")
                for channel in interaction.guild.channels:
                    await channel.set_permissions(role, speak=False, send_messages=False)
            await user.add_roles(role, reason=reason)
            embed = Embed(title="Mute", description=f"{user.mention} has been muted.", color=Colour.red())
            if reason:
                embed.add_field(name="Reason", value=reason)
            await interaction.followup.send(embed=embed)
            await self.add_moderation_log(interaction.guild.id, "mute", user.id, interaction.user.id, reason, datetime.utcnow().timestamp())
        except Exception as e:
            await interaction.channel.send(f"An error occurred: {e}")

    @app_commands.command(name='unmute', description='Unmute a member')
    @app_commands.describe(user='The member to mute')
    @app_commands.checks.has_permissions(administrator=True)
    async def unmute(self, interaction, user: discord.Member):
        await interaction.response.defer()
        try:
            role = get(interaction.guild.roles, name="Muted")
            if role in user.roles:
                await user.remove_roles(role)
                embed = Embed(title="Unmute", description=f"{user.mention} has been unmuted.", color=Colour.green())
                await interaction.followup.send(embed=embed)
            else:
                await interaction.channel.send(f"{user.mention} is not muted.")
        except Exception as e:
            await interaction.channel.send(f"An error occurred: {e}")

    @app_commands.command(name='kick', description='Kick a member from the server')
    @app_commands.describe(user='The member to kick')
    @app_commands.describe(reason='The reason for the kick')
    @app_commands.checks.has_permissions(administrator=True)
    async def kick(self, interaction, user: discord.Member, reason: str = None):
        await interaction.response.defer()
        await user.kick(reason=reason)
        await interaction.followup.send(f"{user.mention} has been kicked for {reason}.")
        await self.db.add_moderation_log(interaction.guild.id, "kick", user.id, interaction.user.id, reason, datetime.utcnow().timestamp())


    @app_commands.command(name='ban', description='Ban a member from the server')
    @app_commands.describe(user='The member to ban')
    @app_commands.describe(reason='The reason for the ban')
    @app_commands.checks.has_permissions(administrator=True)
    async def ban(self, interaction, user: discord.Member, reason: str = None):
        await interaction.response.defer()
        await user.ban(reason=reason)
        await interaction.followup.send(f"{user.mention} has been banned for {reason}.")
        await self.db.add_moderation_log(interaction.guild.id, "ban", user.id, interaction.user.id, reason, datetime.utcnow().timestamp())


    @app_commands.command(name='adjust_roles', description='Add or remove a user\'s role')
    @app_commands.describe(user='The user to adjust the role of')
    @app_commands.describe(action='The action to perform (add or remove)')
    @app_commands.checks.has_permissions(administrator=True)
    async def adjust_roles(self, interaction, user: discord.Member, action: str):
        await interaction.response.defer()

        if action.lower() == 'add':
            # Create a role select menu of all roles in the server
            roles = [role for role in interaction.guild.roles if role != interaction.guild.default_role]
            role_select = discord.ui.RoleSelect(custom_id='role_select_add', roles=roles, placeholder='Select a role to add')

            # Send a message with the role select menu
            await interaction.followup.send("Select a role to add to the user:", components=role_select)

        elif action.lower() == 'remove':
            # Create a role select menu of all roles the user has
            roles = [role for role in user.roles if role != interaction.guild.default_role]
            role_select = discord.ui.RoleSelect(custom_id='role_select_remove', roles=roles, placeholder='Select a role to remove')

            # Send a message with the role select menu
            await interaction.followup.send("Select a role to remove from the user:", components=role_select)

        else:
            await interaction.followup.send("Invalid action. Please enter 'add' or 'remove'.")

    @commands.Cog.listener()
    async def on_role_select_option(self, interaction):
        # Get the selected role and the user
        role = interaction.guild.get_role(interaction.values[0])
        user_id = interaction.message.mentions[0].id
        user = interaction.guild.get_member(user_id)

        if interaction.custom_id == 'role_select_add':
            # If the role select menu for adding a role was used, add the selected role to the user
            await user.add_roles(role)
            await interaction.response.send_message(f"{user.mention} has been given the {role.name} role.")
        elif interaction.custom_id == 'role_select_remove':
            # If the role select menu for removing a role was used, remove the selected role from the user
            await user.remove_roles(role)
            await interaction.response.send_message(f"{user.mention} has been removed from the {role.name} role.")


    @app_commands.command(name='announcement', description='Send an announcement message to all users')
    @app_commands.describe(message='The message to send to all users')
    @app_commands.checks.has_permissions(administrator=True)
    async def send_message(self, interaction, *, message: str = None):
        await interaction.response.defer()
        for member in interaction.guild.members:
            if not member.bot:
                await member.send(message)

    async def add_moderation_log(self, guild_id, action, user_id, moderator_id, reason, timestamp):
        await self.bot.db.c.execute(f"""
            INSERT INTO moderation_logs_{guild_id}(action, user_id, moderator_id, reason, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (action, user_id, moderator_id, reason, timestamp))
        await self.bot.db.conn.commit()

    @commands.Cog.listener()
    async def on_channel_create(self, channel):
        """Ensure the Muted role has the correct permissions in new channels."""
        muted_role = get(channel.guild.roles, name="Muted")
        if muted_role:
            await channel.set_permissions(muted_role, speak=False, send_messages=False)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message is from a bot
        if message.author.bot:
            return
        support_channel = await self.bot.db.get_support_channel_name(message.guild.id)
        # Check if the message is in the support channel
        if message.channel.name == support_channel:
            return
        # Check for keywords
        keywords = ["help", "support", "assist"]
        if any(keyword in message.content.lower() for keyword in keywords):
            await message.reply(f"If you are looking for help or support, please go to the #support channel.")


def setup(bot, db_cog):
    bot.add_cog(AdminControls(bot, db_cog))
