from discord.ext import commands
from discord.utils import get
import discord
import datetime
from discord import app_commands, Embed, Colour
from discord.ui import Modal, TextInput, Select

class SetupSelect(Select):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

    async def callback(self, interaction):
        selection = self.values[0]

        match selection:
            case "Add FAQ":
                view = AddFAQModal(self.bot)
                await interaction.response.send_modal(view)
            
            case "Remove FAQ":
                # Fetch all FAQs from database
                database_cog = self.bot.get_cog("Database")
                all_faqs = await database_cog.get_all_faqs(interaction.guild.id)

                faq_msg = "\n".join([f"#{faq[0]} - {faq[1]}" for faq in all_faqs])
                await interaction.response.send_message(f"FAQs:\n{faq_msg}", ephemeral=True)
                
                # Create a select menu with all FAQ numbers
                select = FAQRemoveSelect(self.bot, custom_id="faq_remove_selection", placeholder="Select a FAQ to remove")
                select.options = [discord.SelectOption(label=str(faq[0]), value=str(faq[0])) for faq in all_faqs]
                view = discord.ui.View()
                view.add_item(select)
                await interaction.followup.send("Select a FAQ to remove:", view=view, ephemeral=True)
                
            case "Set Role":
                database_cog = self.bot.get_cog("Database")
                role_names = await database_cog.get_predefined_role_names(interaction.guild.id)
                select = ServerRoleSelect(self.bot, custom_id="server_role_selection", placeholder="Select a predefined role name")
                select.options = [discord.SelectOption(label=role_name, value=role_name) for role_name in role_names]
                view = discord.ui.View()
                view.add_item(select)
                await interaction.response.send_message("Select a predefined role name:", view=view, ephemeral=True)

            case "Set Channel":
                server_channels = interaction.guild.text_channels
                select = ServerChannelSelect(custom_id="server_channel_selection", placeholder="Select a server channel")
                select.options = [discord.SelectOption(label=channel.name, value=str(channel.id)) for channel in server_channels]
                view = discord.ui.View()
                view.add_item(select)
                await interaction.response.send_message("Select a server channel:", view=view, ephemeral=True)

            # TODO: Add other admin commands
            case _:
                await interaction.response.send_message("Invalid selection.", ephemeral=True)

class FAQRemoveSelect(Select):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

    async def callback(self, interaction):
        faq_number = int(self.values[0])
        try:
            database_cog = self.bot.get_cog("Database")
            await database_cog.remove_faq(faq_number, interaction.guild.id)

            await interaction.response.send_message(f"FAQ #{faq_number} has been removed successfully.", ephemeral=True)
            print(f"FAQ #{faq_number} has been removed successfully.")
        except Exception as e:
            await interaction.response.send_message(f"Error removing FAQ: {e}", ephemeral=True)
            print(f"Error removing FAQ: {e}")

class AddFAQModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Add FAQ")
        self.bot = bot
        
        # Creating input fields for FAQ Number and Content
        self.number_input = TextInput(label='Enter FAQ number and title',
                                            style=discord.TextStyle.short,
                                            placeholder=f'Example: #1 Pateron Support', # maybe add a list of current FAQ numbers
                                            min_length=1,
                                            max_length=45,
                                            required=True)
        self.content_input = TextInput(label='Enter the FAQ content',
                                            style=discord.TextStyle.long,
                                            placeholder=f'Enter the FAQ content',
                                            min_length=1,
                                            max_length=4000,
                                            required=True)
        
        # Add the TextInput components to the modal
        self.add_item(self.number_input)
        self.add_item(self.content_input)

    async def on_submit(self, interaction):
        number = int(self.number_input.value)
        content = self.content_input.value
        try:
            database_cog = self.bot.get_cog("Database")
            await database_cog.add_faq(number, content, interaction.guild.id)

            await interaction.response.send_message(f"FAQ #{number} has been added successfully.", ephemeral=True)
            print(f"FAQ #{number} has been added successfully.")
        except Exception as e:
            await interaction.response.send_message(f"Error adding FAQ: {e}", ephemeral=True)
            print(f"Error adding FAQ: {e}")


class ServerRoleSelect(Select):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

    async def callback(self, interaction):
        try:
            selected_predefined_role_name = self.values[0]
            predefined_role_name = selected_predefined_role_name
            
            # Create another select menu for the user to choose an actual role
            server_roles = interaction.guild.roles
            select = ActualRoleSelect(self.bot, predefined_role_name, custom_id="actual_role_selection", placeholder="Select a server role")
            select.options = [discord.SelectOption(label=role.name, value=str(role.id)) for role in server_roles]
            view = discord.ui.View()
            view.add_item(select)
            await interaction.response.send_message(f"Link the predefined role '{selected_predefined_role_name}' to:", view=view, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error setting server role: {e}", ephemeral=True)
            print(f"Error setting server role: {e}")

class ActualRoleSelect(Select):
    def __init__(self, bot, predefined_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.predefined_name = predefined_name

    async def callback(self, interaction):
        selected_server_role_id = int(self.values[0])
        role = discord.utils.get(interaction.guild.roles, id=selected_server_role_id)
        
        if role:
            # Update the role in the database
            try:
                # Assuming the role name is constant and known. If not, we can modify this.
                database_cog = self.bot.get_cog("Database")
                await database_cog.set_server_role(interaction.guild.id, self.predefined_name, role.name, role.id)

                await interaction.response.send_message(f"Role linked to {role.name}.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"Error updating role in database: {e}", ephemeral=True)
                print(f"Error updating role in database: {e}")
        else:
            await interaction.response.send_message(f"Error: Role not found.", ephemeral=True)
            print(f"Error: Role not found.")


class ServerChannelSelect(Select):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def callback(self, interaction):
        selected_server_channel_id = int(self.values[0])
        channel = interaction.guild.get_channel(selected_server_channel_id)
        
        if channel:
            # The logic for updating the channel in the database was not provided in the original code.
            # Placeholder logic is provided here; it may be replaced with the actual logic when available.
            await interaction.response.send_message(f"Channel {channel.mention} set.", ephemeral=True)
            print(f"Channel {channel.mention} set.")
        else:
            await interaction.response.send_message(f"Error: Channel not found.", ephemeral=True)
            print(f"Error: Channel not found.")

class AdminControls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='setup', description='Press ENTER to setup the bot.')
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction):
        commands = ["Add FAQ", "Remove FAQ", "Set Role", "Set Channel"]
        select = SetupSelect(self.bot, custom_id="setup_command", placeholder="Select a Command")
        select.options = [discord.SelectOption(label=command, value=command) for command in commands]
        view = discord.ui.View()
        view.add_item(select)
        await interaction.response.send_message("Select an Admin Command", view=view, ephemeral=True)

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
            await interaction.channel.send(f"An error occurred: {e}", ephemeral=True)
            print(f"An error occurred: {e}")

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
                await interaction.channel.send(f"{user.mention} is not muted.", ephemeral=True)
                print(f"{user.mention} is not muted.")
        except Exception as e:
            await interaction.channel.send(f"An error occurred: {e}")
            print(f"An error occurred: {e}")

    @app_commands.command(name='kick', description='Kick a member from the server')
    @app_commands.describe(user='The member to kick')
    @app_commands.describe(reason='The reason for the kick')
    @app_commands.checks.has_permissions(administrator=True)
    async def kick(self, interaction, user: discord.Member, reason: str = None):
        try:
            await interaction.response.defer()
            await user.kick(reason=reason)
            await interaction.followup.send(f"{user.mention} has been kicked for {reason}.")
            await self.db.add_moderation_log(interaction.guild.id, "kick", user.id, interaction.user.id, reason, datetime.utcnow().timestamp())
        except Exception as e:
            await interaction.channel.send(f"An error occurred: {e}", ephemeral=True)
            print(f"An error occurred: {e}")

    @app_commands.command(name='ban', description='Ban a member from the server')
    @app_commands.describe(user='The member to ban')
    @app_commands.describe(reason='The reason for the ban')
    @app_commands.checks.has_permissions(administrator=True)
    async def ban(self, interaction, user: discord.Member, reason: str = None):
        try:
            await interaction.response.defer()
            await user.ban(reason=reason)
            await interaction.followup.send(f"{user.mention} has been banned for {reason}.")
            await self.db.add_moderation_log(interaction.guild.id, "ban", user.id, interaction.user.id, reason, datetime.utcnow().timestamp())
        except Exception as e:
            await interaction.channel.send(f"An error occurred: {e}", ephemeral=True)
            print(f"An error occurred: {e}")

    @app_commands.command(name='adjust_roles', description='Add or remove a user\'s role')
    @app_commands.describe(user='The user to adjust the role of')
    @app_commands.describe(action='The action to perform (add or remove)')
    @app_commands.checks.has_permissions(administrator=True)
    async def adjust_roles(self, interaction, user: discord.Member, action: str):
        await interaction.response.defer()
        try:
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
        except Exception as e:
            await interaction.channel.send(f"An error occurred: {e}", ephemeral=True)
            print(f"An error occurred: {e}")

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
        keywords = ["help", "support", "assist", "pack"]
        if any(keyword in message.content.lower() for keyword in keywords):
            await message.reply(f"If you are looking for help or support, please go to the #support channel.")


async def setup(bot):
    await bot.add_cog(AdminControls(bot))
