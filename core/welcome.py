import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Button, View, Modal, TextInput
from datetime import datetime, timedelta

class RoleButton(Button):
    cooldown_users = {}

    def __init__(self, label, role_id, emoji=None):
        super().__init__(label=label, custom_id=str(role_id), emoji=emoji)
        self.role_id = role_id

    async def callback(self, interaction):
        if interaction.user.id in self.cooldown_users:
            if datetime.utcnow() < self.cooldown_users[interaction.user.id]:
                await interaction.response.send_message(f"Don't spam the buttons!", ephemeral=True)
                return

        role = interaction.guild.get_role(int(self.role_id))
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"Removed {self.label} role!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"Added {self.label} role!", ephemeral=True)

        # Add a 10-second cooldown (can be adjusted)
        self.cooldown_users[interaction.user.id] = datetime.utcnow() + timedelta(seconds=10)

class WelcomePageModal(Modal):
    def __init__(self, bot, interaction, role_mapping):
        super().__init__(title="Setup Welcome Page")
        self.bot = bot
        self.interaction = interaction
        self.role_mapping = role_mapping

        default_txt = [channel.name for channel in interaction.guild.text_channels]
        default_txt_str = "\n".join(default_txt)
        
        self.channel_name = TextInput(label='Enter 1 channel name exactly as it appears',
                                       style=discord.TextStyle.long,
                                       placeholder='Welcome to our server! Please select your roles...',
                                       default=f'Delete all text but the exact name of the channel \n {default_txt}',
                                       min_length=1,
                                       max_length=4000,
                                       required=True)
        self.message_input = TextInput(label='Enter the welcome message',
                                       style=discord.TextStyle.long,
                                       placeholder='Welcome to our server! Here is a list of rules. Please select your roles...',
                                       min_length=1,
                                       max_length=4000,
                                       required=True)
        
        self.add_item(self.channel_name)
        self.add_item(self.message_input)

    async def on_submit(self, interaction):
        welcome_msg = self.message_input.value
        welcome_channel = self.channel_name.value
        if not welcome_channel:
            await interaction.response.send_message("Please enter a valid channel name!", ephemeral=True)
            print("No valid channel name entered")
            return
        
        database_cog = self.bot.get_cog("Database")
        view = RulesView(database_cog, self.interaction.guild.id, self.role_mapping)
        channel = discord.utils.get(self.interaction.guild.text_channels, name=welcome_channel)
        if channel:
            await channel.send(content=welcome_msg, view=view)
            await interaction.response.send_message("Welcome page created successfully!", ephemeral=True)
        else:
            await interaction.response.send_message("Channel not found!", ephemeral=True)
            return

class RulesView(View):
    def __init__(self, database_cog, guild_id, role_mapping):
        super().__init__(timeout=None)
        self.database = database_cog
        
        for role_name, role_info in role_mapping.items():
            self.add_item(RoleButton(label=role_name, role_id=role_info['id'], emoji=role_info['emoji']))

class WelcomeNewUser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        rules_channel = discord.utils.get(member.guild.text_channels, name="rules")
        msg = f"Welcome {member.mention}! Please head over to {rules_channel.mention} to get your roles."
        await member.send(msg)  # Send a DM to the new member

    @app_commands.command(name="create_welcome_page", description="Create a welcome page for new members.")
    @app_commands.checks.has_permissions(administrator=True)
    async def create_welcome_page(self, interaction):
        role_mapping, unmapped_roles = await self.get_role_mapping(interaction.guild.id)
        if unmapped_roles:
            await interaction.response.defer()
            unmapped_str = ', '.join(unmapped_roles)
            await interaction.followup.send(
                f"The following roles are not properly mapped in the database: {unmapped_str}. Please use the /setup command to map them before continuing.",
                ephemeral=True)
            return
        
        view = WelcomePageModal(self.bot, interaction, role_mapping)
        await interaction.response.send_modal(view)

    async def get_role_mapping(self, guild_id):
        # Role names that we expect to find in the database
        expected_roles = [
            "Read the Rules",
            "Patreon Announcements",
            "Announcements",
            "Behind the Scenes",
            "Showcase"
        ]

        # Fetch mappings from the database
        db_cog = self.bot.get_cog("Database")
        unmapped_roles = []
        role_mapping = {}

        for role_name in expected_roles:
            role_id = await db_cog.get_server_role(guild_id, role_name)
            if role_id:
                print(f"Found mapping for {role_name}")
                role_mapping[role_name] = {'id': role_id, 'emoji': "📜"}
            else:
                print(f"Did not find mapping for {role_name}")
                unmapped_roles.append(role_name)

        return role_mapping, unmapped_roles

async def setup(bot):
    await bot.add_cog(WelcomeNewUser(bot))