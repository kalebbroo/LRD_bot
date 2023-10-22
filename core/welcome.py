import discord
from discord import app_commands, Colour
from discord.ext import commands, tasks
from discord.ui import Button, View, Modal, TextInput
from datetime import datetime, timedelta
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

        for button_name, role_info in role_mapping.items():
            # Pass the bot instance when creating the RoleButton
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
        db_cog = self.bot.get_cog("Database")
        embed_cog = self.bot.get_cog("CreateEmbed")
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
            embed = await embed_cog.create_embed(title="Welcome", description=f"Welcome {member.mention}! Please head over to {welcome_channel.mention} to get your roles.", color=Colour.blue())
            await general_channel.send(embed=embed)
        else:
            embed = await embed_cog.create_embed(title="Welcome", description=f"Welcome to {member.guild.name}! Please check out {welcome_channel.mention} to get your roles.", color=Colour.blue())
            await member.send(embed=embed)


    async def refresh_welcome_message(self, guild_id):
        db_cog = self.bot.get_cog("Database")
        create_embed_cog = self.bot.get_cog("CreateEmbed")
        welcome_channel_name = await db_cog.get_welcome_channel(guild_id)
        welcome_msg = await db_cog.get_welcome_message(guild_id)
        guild = self.bot.get_guild(guild_id)

        if not welcome_channel_name:
            print(f"No welcome channel set for {guild.name}. Skipping welcome message refresh.")
            # Fetch the CreateEmbed cog to create the embed
            embed = await create_embed_cog.create_embed(
                title="Bot Setup Required",
                description="""The bot has joined the server but it has not been setup.
                Please use the `/setup` command to configure the bot. Or the `/help setup` command to see detailed instructions.
                - First, you will need to create the role buttons and map a role to them. These are the buttons that users will click to get their roles.
                - Second, you will need to map the channel names to the database. These are the channels where the messages will be posted.
                - Third, you will need to set up the welcome/rules page. This message should explain the rules of the server and instruct users to click the buttons to get their roles.
                - Lastly, you will need to add the FAQ entries. These are the FAQs that admins can send to users when they ask questions.
                
                **Bonus:** Retroactively add XP to users who have been active in the server before the bot was added. This should only be ran once and is dangerous.

                **Note:** The bot will not work until the setup is complete.
                """,
                footer_text = "Please contact Kalebbroo if you need help.",
                color=discord.Colour.red()
            )
            for member in guild.members:
                # Check if the member has the Administrator permission
                if member.guild_permissions.administrator:
                    try:
                        # Send the embed
                        await member.send(embed=embed)
                    except discord.HTTPException:
                        # Handle any exceptions that arise from sending the DM (e.g., DMs blocked)
                        print(f"Failed to send DM to {member.name}")
            return

        if not welcome_msg or welcome_msg.strip() == "":
            print(f"No welcome message set for {guild.name}. Skipping welcome message send.")
            return

        # Fetch the channel ID from the database based on the channel's display name
        welcome_channel_id = await db_cog.get_id_from_display(guild_id, welcome_channel_name)
        welcome_channel = self.bot.get_channel(welcome_channel_id)
        if not welcome_channel:
            print(f"No channel named {welcome_channel_name} found in {guild.name}")
            return

        # Create the embed
        embed = await create_embed_cog.create_embed(
            title="Welcome to the LittleRoomDev Official Discord Server!",
            description=welcome_msg,
            color=discord.Colour.green()
        )
        # Delete the last message in the welcome channel
        try:
            last_message = await welcome_channel.fetch_message(welcome_channel.last_message_id)
            if last_message.author == self.bot.user:  # Ensure the last message was sent by the bot
                await last_message.delete()
        except Exception as e:
            print(f"Error deleting the last message: {e}")

        # Repost the welcome message with the buttons
        role_mapping, _ = await self.get_role_mapping(guild_id)
        view = RulesView(self.bot, db_cog, guild_id, role_mapping)
        await welcome_channel.send(embed=embed, view=view)


    async def get_role_mapping(self, guild_id):
        db_cog = self.bot.get_cog("Database")
        
        button_names = await db_cog.get_button_names(guild_id)
        unmapped_buttons = []
        role_mapping = {}

        for btn_name in button_names:
            role_info = await db_cog.get_server_role(guild_id, btn_name)
            if role_info:
                #print(f"Found mapping for {btn_name}")
                role_mapping[btn_name] = {'role_id': role_info['role_id'], 'emoji': role_info['emoji']}
            else:
                print(f"Did not find mapping for {btn_name}")
                unmapped_buttons.append(btn_name)

        return role_mapping, unmapped_buttons

async def setup(bot):
    await bot.add_cog(WelcomeNewUser(bot))
