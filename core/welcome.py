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
        welcome_channel_name = self.channel_name.value

        channel = discord.utils.get(interaction.guild.text_channels, name=welcome_channel_name)
        if not channel:
            await interaction.response.send_message("Please enter a valid channel name!", ephemeral=True)
            return

        database_cog = self.bot.get_cog("Database")
        await database_cog.set_channel_mapping(interaction.guild.id, welcome_channel_name, channel.name, channel.id, welcome_msg)

        print(self.role_mapping)
        
        view = RulesView(database_cog, interaction.guild.id, self.role_mapping)
        await channel.send(content=welcome_msg, view=view)
        await interaction.response.send_message("Welcome page created successfully!", ephemeral=True)


class RulesView(View):
    def __init__(self, database_cog, guild_id, role_mapping):
        super().__init__(timeout=None)
        self.database = database_cog

        # Update to use the new role_mapping structure
        for button_name, role_info in role_mapping.items():
            print(f"Adding button: {button_name}, Role ID: {role_info['role_id']}, Emoji: {role_info['emoji']}")
            self.add_item(RoleButton(label=button_name, role_id=role_info['role_id'], emoji=role_info['emoji']))



class WelcomeNewUser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        db_cog = self.bot.get_cog("Database")
        # Get the channel name set in the database
        welcome_channel_name = await db_cog.get_welcome_channel(member.guild.id)
        # If there's no channel set, enter the default fallback channel name. This can be changed to whatever you want.
        if not welcome_channel_name:
            welcome_channel_name = "rules"

        welcome_channel = discord.utils.get(member.guild.text_channels, name=welcome_channel_name)
        
        if not welcome_channel:
            print(f"No channel named {welcome_channel_name} found in {member.guild.name}")
            return
        # Get the default system channel for the guild
        general_channel = member.guild.system_channel
        if general_channel:
            await general_channel.send(f"Welcome {member.mention}! Please head over to {welcome_channel.mention} to get your roles.")
        else:
            await member.send(f"Welcome to {member.guild.name}! Please check out {welcome_channel.mention} to get your roles.")

    async def refresh_welcome_message(self, guild_id):
        db_cog = self.bot.get_cog("Database")
        # Get the channel name you've set in the database
        welcome_channel_name = await db_cog.get_welcome_channel(guild_id)
        welcome_msg = await db_cog.get_welcome_message(guild_id)
        # Fetch the guild
        guild = self.bot.get_guild(guild_id)
        # If there's no channel set, you can default to a channel named "rules"
        if not welcome_channel_name:
            welcome_channel_name = "rules"
        welcome_channel = discord.utils.get(guild.text_channels, name=welcome_channel_name)
        if not welcome_channel:
            print(f"No channel named {welcome_channel_name} found in {guild.name}")
            return
        # Delete the last message in the welcome channel
        try:
            last_message = await welcome_channel.fetch_message(welcome_channel.last_message_id)
            if last_message.author == self.bot.user:  # Ensure the last message was sent by the bot
                await last_message.delete()
        except Exception as e:
            print(f"Error deleting the last message: {e}")
        # Repost the welcome message with the buttons
        role_mapping, _ = await self.get_role_mapping(guild_id)
        view = RulesView(db_cog, guild_id, role_mapping)
        await welcome_channel.send(content=welcome_msg, view=view)

    async def get_role_mapping(self, guild_id):
        db_cog = self.bot.get_cog("Database")
        
        button_names = await db_cog.get_button_names(guild_id)
        unmapped_buttons = []
        role_mapping = {}

        for btn_name in button_names:
            role_info = await db_cog.get_server_role(guild_id, btn_name)
            if role_info:
                print(f"Found mapping for {btn_name}")
                role_mapping[btn_name] = {'role_id': role_info['role_id'], 'emoji': role_info['emoji']}
            else:
                print(f"Did not find mapping for {btn_name}")
                unmapped_buttons.append(btn_name)

        return role_mapping, unmapped_buttons

async def setup(bot):
    await bot.add_cog(WelcomeNewUser(bot))
