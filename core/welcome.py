import discord
from discord import app_commands, Colour
from discord.ext import commands, tasks
from discord.ui import Button, View, Modal, TextInput
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

class RoleButton(Button):
    cooldown_users = {}

    def __init__(self, bot, label, role_id, emoji=None):
        super().__init__(label=label, custom_id=str(role_id), emoji=emoji)
        self.bot = bot
        self.role_id = role_id

    async def callback(self, interaction):
        embed_cog = self.bot.get_cog("CreateEmbed")
        if interaction.user.id in self.cooldown_users:
            if datetime.utcnow() < self.cooldown_users[interaction.user.id]:
                embed = await embed_cog.create_embed(title="Error", description="Don't spam the buttons!", color=Colour.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        role = interaction.guild.get_role(int(self.role_id))
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"Removed {self.label} role!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"Added {self.label} role!", ephemeral=True)

        # Add a 3-second cooldown (can be adjusted)
        self.cooldown_users[interaction.user.id] = datetime.utcnow() + timedelta(seconds=3)


class RulesView(View):
    def __init__(self, bot, database_cog, guild_id, role_mapping):
        super().__init__(timeout=None)
        self.database = database_cog
        self.bot = bot
        # Get the role mapping from the database
        for button_name, role_info in role_mapping.items():
            self.add_item(RoleButton(self.bot, label=button_name, role_id=role_info['role_id'], emoji=role_info['emoji']))

class WelcomeNewUser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class SetupModal(Modal):
        def __init__(self, bot, interaction, role_mapping=None, channel=None, modal_type="welcome"):
            super().__init__(title=f"Setup {modal_type.capitalize()} Page")
            self.bot = bot
            self.interaction = interaction
            self.role_mapping = role_mapping
            self.channel = channel
            self.modal_type = modal_type

            self.message_input1 = TextInput(label='Enter the first message',
                                            style=discord.TextStyle.long,
                                            placeholder='First message...',
                                            min_length=1,
                                            max_length=4000,
                                            required=True)
            self.message_input2 = TextInput(label='Enter the second message',
                                            style=discord.TextStyle.long,
                                            placeholder='Second message...',
                                            min_length=1,
                                            max_length=4000,
                                            required=True)
            self.message_input3 = TextInput(label='Enter the third message',
                                            style=discord.TextStyle.long,
                                            placeholder='Third message...',
                                            min_length=1,
                                            max_length=4000,
                                            required=True)
            self.message_input4 = TextInput(label='Enter the fourth message',
                                            style=discord.TextStyle.long,
                                            placeholder='Fourth message...',
                                            min_length=1,
                                            max_length=4000,
                                            required=True)

            self.add_item(self.message_input1)
            self.add_item(self.message_input2)
            self.add_item(self.message_input3)
            self.add_item(self.message_input4)

        async def on_submit(self, interaction):
            embed_cog = self.bot.get_cog("CreateEmbed")
            database_cog = self.bot.get_cog("Database")
            support_cog = self.bot.get_cog("Support")

            msg1 = self.message_input1.value
            msg2 = self.message_input2.value
            msg3 = self.message_input3.value
            msg4 = self.message_input4.value

            if self.modal_type == "welcome":
                fields = [("Basic Common Sense", msg1, True),
                        ("Admins and Bots", msg2, True),
                        ("How to get Support", msg3, True),
                        ("Server Specific Rules", msg4, True)]
                embed_data = {
                    "title": f"{self.modal_type.capitalize()} to the LittleRoomDev Official Discord Server!",
                    "description": f"These are the server rules. Please read them carefully and click the buttons below to add or remove roles.",
                    "color": Colour.green().value,
                    "fields": fields
                }
                embed = await embed_cog.create_embed(**embed_data)
                embed_data_str = json.dumps(embed_data)
                view = RulesView(self.bot, database_cog, interaction.guild.id, self.role_mapping)
                sent_message = await self.channel.send(embed=embed, view=view)
                await interaction.response.send_message("Welcome page has been set up successfully!", ephemeral=True)
            else:
                fields = [("Common Issues", msg1, True),
                        ("Create A Support Ticket", msg2, True),
                        ("Report A User", msg3, True),
                        ("Commission Requests", msg4, True)]
                embed_data = {
                    "title": f"Welcome to the LittleRoomDev {self.modal_type.capitalize()} page!",
                    "description": f"Before making a ticket or request please read the following, then click the approporate button below.",
                    "color": Colour.green().value,
                    "fields": fields
                }
                embed = await embed_cog.create_embed(**embed_data)
                embed_data_str = json.dumps(embed_data)
                view = support_cog.TicketButton(self.bot, interaction)
                sent_message = await self.channel.send(embed=embed, view=view)
                await interaction.response.send_message("Support page has been set up successfully!", ephemeral=True)

            await database_cog.set_channel_mapping(interaction.guild.id, self.channel.name.capitalize(), self.channel.name, self.channel.id, embed_data_str, sent_message.id)
            # TODO: make the channel setup only choose the channel then it should set the display name as same as the channel just uppercase and the id as the channel id

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Fetch Database and Embed cogs
        db_cog = self.bot.get_cog("Database")
        embed_cog = self.bot.get_cog("CreateEmbed")

        # Fetch welcome channel name from the database
        welcome_channel_name = await db_cog.handle_channel(member.guild.id, "get_welcome_channel")

        if welcome_channel_name:
            # Find the welcome channel in the guild using the fetched name
            welcome_channel = discord.utils.get(member.guild.text_channels, name=welcome_channel_name)
        else:
            print(f"No welcome channel name found in the database for {member.guild.name}")
            return
        if not welcome_channel:
            print(f"No channel named {welcome_channel_name} found in {member.guild.name}")
            return

        # Construct the welcome message embed
        embed_title = "Welcome"
        embed_description = f"Welcome <@{member.id}> to {member.guild.name}! Please check out {welcome_channel.mention} to get your roles."
        embed_color = discord.Colour.blue()
        welcome_embed = await embed_cog.create_embed(title=embed_title, description=embed_description, color=embed_color)

        # Send the welcome message to the guild's system channel, if available; otherwise, send it to the user directly
        general_channel = member.guild.system_channel
        if general_channel:
            await general_channel.send(embed=welcome_embed)
        else:
            await member.send(embed=welcome_embed)


    async def setup_message(self, guild_id):
        create_embed_cog = self.bot.get_cog("CreateEmbed")
        embed = await create_embed_cog.create_embed(
            title="Bot Setup Required",
            description = (
                "The bot has joined the server but it has not been set up.\n"
                "Please use the `/setup` command to configure the bot. Or the `/help setup` command to see detailed instructions.\n"
                "1. First, you will need to create the role buttons and map a role to them. These are the buttons that users will click to get their roles.\n"
                "2. Second, you will need to map the channel names to the database. These are the channels where the messages will be posted.\n"
                "3. Third, you will need to set up the welcome/rules page. This message should explain the rules of the server and instruct users to click the buttons to get their roles.\n"
                "4. Lastly, you will need to add the FAQ entries. These are the FAQs that admins can send to users when they ask questions.\n\n"
                "**Bonus:** Retroactively add XP to users who have been active in the server before the bot was added. This should only be run once and is dangerous.\n\n"
                "**Note:** The bot will not work until the setup is complete."
            ),
            footer_text="Please contact Kalebbroo if you need help.",
            color=discord.Colour.red()
        )
        guild = self.bot.get_guild(guild_id)
        # Send the embed to users who have the admin role and are not bots
        for member in guild.members:
            if not member.bot:  # Check if the member is not a bot
                for role in member.roles:
                    if role.name == "Admin":
                        try:
                            await member.send(embed=embed)
                        except discord.HTTPException:
                            # Handle any exceptions that arise from sending the DM (e.g., DMs blocked)
                            print(f"Failed to send DM to {member.name}")

    async def get_role_mapping(self, guild_id: int) -> Tuple[Dict[str, Dict[str, str]], List[str]]:
        db_cog = self.bot.get_cog("Database")
        role_mapping = {}
        unmapped_buttons = []

        # Fetch all the button names mapped in the database for this guild
        button_display_names = await db_cog.handle_server_role(guild_id, "get_all_button_names")

        for btn_name in button_display_names:
            role_info = await db_cog.handle_server_role(guild_id, "get", button_name=btn_name)
            if role_info:
                # role_info is a tuple, so we need to access its elements by index
                role_id, emoji = role_info
                role_mapping[btn_name] = {'role_id': role_id, 'emoji': emoji}
            else:
                unmapped_buttons.append(btn_name)

        return role_mapping, unmapped_buttons

async def setup(bot):
    await bot.add_cog(WelcomeNewUser(bot))
