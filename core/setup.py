import discord
from discord.ext import commands
from discord import app_commands, Embed, Colour
from discord.ui import Modal, TextInput, Select
import asyncio
import random
import json

class SetupSelect(Select):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

    async def callback(self, interaction):
        selection = self.values[0]
        embed_cog = self.bot.get_cog("CreateEmbed")
        db_cog = self.bot.get_cog("Database")

        match selection:
            case "Add FAQ":
                view = AddFAQModal(self.bot)
                await interaction.response.send_modal(view)
            
            case "Remove FAQ":
                all_faqs = await db_cog.handle_faq(interaction.guild.id, "get_all")
                faq_msg = "\n".join([f"#{faq[0]} - {faq[1]}" for faq in all_faqs])
                embed = await embed_cog.create_embed(title="FAQs", description=faq_msg, color=Colour.blue())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                select = FAQRemoveSelect(self.bot, custom_id="faq_remove_selection", placeholder="Select a FAQ to remove")
                select.options = [discord.SelectOption(label=str(faq[0]), value=str(faq[0])) for faq in all_faqs]
                view = discord.ui.View()
                view.add_item(select)
                await interaction.followup.send("Select a FAQ to remove:", view=view, ephemeral=True)
                
            case "Map Roles and Create Buttons":
                select_menu = RoleSelect(self.bot, interaction.guild.roles)
                view = discord.ui.View()
                view.add_item(select_menu)
                await interaction.response.send_message("Please select a role to map", view=view, ephemeral=True)

            case "Map Channel Names to Database":
                select_menu = MapChannelSelect(self.bot, interaction.guild)
                view = discord.ui.View()
                view.add_item(select_menu)
                await interaction.response.send_message("Please select a channel to map", view=view, ephemeral=True)

            case "Welcome Page Setup":
                # Using Database cog's handle_channel method
                channel_names = await db_cog.handle_channel(interaction.guild.id, "get_display_names")
                print(f"\nChannel names: {channel_names}\n")
                if not channel_names:
                    await interaction.response.send_message("No channels are available for mapping. Please set up channels first.", ephemeral=True)
                    return
                select_menu = ChannelSelect(self.bot, channel_names, interaction.guild.id, "welcome")
                view = discord.ui.View()
                view.add_item(select_menu)
                await interaction.response.send_message("Please select a welcome channel:", view=view, ephemeral=True)

            case "Support Ticket Setup":
                # Using Database cog's handle_channel method
                channel_names = await db_cog.handle_channel(interaction.guild.id, "get_display_names")
                if not channel_names:
                    await interaction.response.send_message("No channels are available for mapping. Please set up channels first.", ephemeral=True)
                    return
                select_menu = ChannelSelect(self.bot, channel_names, interaction.guild.id, "support")
                view = discord.ui.View()
                view.add_item(select_menu)
                await interaction.response.send_message("Please select a support channel:", view=view, ephemeral=True)

            case "Retroactively Add XP":
                embed = await embed_cog.create_embed(title="Retroactively Adding XP", 
                                                     description="Started the process, this may take some time.", 
                                                     color=Colour.blue())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                print("Beginning XP addition based on message history. This may take some time.")
                # Loop through all text channels in the server
                for channel in interaction.guild.text_channels:
                    try:
                        # Fetch messages from the channel using history
                        async for message in channel.history(limit=None):  # `limit=None` fetches all messages
                            # Fetch user data from the new Database cog
                            user_data = await db_cog.handle_user(interaction.guild.id, 'get', user_id=message.author.id)
                            # Check if user_data is not None before proceeding
                            if user_data is None:
                                continue
                            # Update message count
                            user_data['message_count'] += 1
                            # Add XP to the user
                            xp = random.randint(5, 50)
                            user_data['xp'] += xp
                            # Update the user data in the new Database cog
                            await db_cog.handle_user(interaction.guild.id, 'update', user_data=user_data)
                        # Sleep for a short duration to prevent rate limits
                        await asyncio.sleep(0.2)
                    except Exception as e:
                        print(f"Error fetching messages from channel {channel.name}: {e}")
                print("Finished adding XP based on message history.")

            # TODO: Add other admin commands
            case _:
                embed = await embed_cog.create_embed(title="Error", description="Invalid selection.", color=Colour.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)


class FAQRemoveSelect(Select):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

    async def callback(self, interaction):
        # Convert the selected FAQ number to integer
        faq_number = int(self.values[0])
        try:
            # Get the Database cog and remove the FAQ from the database
            database_cog = self.bot.get_cog("Database")
            await database_cog.handle_faq(interaction.guild.id, "remove", number=faq_number)

            # Send a success message
            await interaction.response.send_message(f"FAQ #{faq_number} has been removed successfully.", ephemeral=True)
            print(f"FAQ #{faq_number} has been removed successfully.")
        except Exception as e:
            # Send an error message in case of exceptions
            await interaction.response.send_message(f"Error removing FAQ: {e}", ephemeral=True)
            print(f"Error removing FAQ: {e}")

class AddFAQModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Add FAQ")
        self.bot = bot
        
        # Creating input fields for FAQ Number and Content
        self.number_input = TextInput(label='Enter FAQ number',
                              style=discord.TextStyle.short,
                              placeholder=f'Example: 1',
                              min_length=1,
                              max_length=10,
                              required=True)
        self.name_input = TextInput(label='Enter FAQ name',
                                    style=discord.TextStyle.short,
                                    placeholder=f'Example: Patreon Support',
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
        self.add_item(self.name_input)
        self.add_item(self.content_input)

    async def on_submit(self, interaction):
        try:
            # Get the entered FAQ information
            number = int(self.number_input.value)
            name = self.name_input.value
            content = self.content_input.value
            # Get the Database and Embed cogs
            database_cog = self.bot.get_cog("Database")
            embed_cog = self.bot.get_cog("CreateEmbed")

            # Check if the FAQ already exists
            existing_faq = await database_cog.handle_faq(interaction.guild.id, "get", number=number)

            if existing_faq:
                # Send an error message if the FAQ exists
                embed = await embed_cog.create_embed(title="Error", description=f"FAQ #{number} already exists. Choose another number.", color=Colour.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Add the new FAQ to the database
            await database_cog.handle_faq(interaction.guild.id, "add", number=number, name=name, content=content)

            # Send a success message
            embed = await embed_cog.create_embed(title="Success", description=f"FAQ #{number} - {name} has been added successfully.", color=Colour.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            # Handle ValueError for incorrect FAQ number
            embed = await embed_cog.create_embed(title="Error", description=f"Please enter a valid number for the FAQ.", color=Colour.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            # Handle general exceptions
            embed = await embed_cog.create_embed(title="Error", description=f"Error adding FAQ: {e}", color=Colour.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)


class RoleMappingModal(Modal):
    def __init__(self, bot, guild, role):
        super().__init__(title="Map Roles and Create Buttons")
        self.role = role
        self.bot = bot
        
        # Creating input fields for role and button mapping
        self.button_name_input = TextInput(label='Enter the button display name',
                                           style=discord.TextStyle.short,
                                           placeholder='Example: Patreon Support',
                                           min_length=1,
                                           max_length=100,
                                           required=True)
        self.emoji_input = TextInput(label='Enter the emoji for the button',
                                     style=discord.TextStyle.short,
                                     default='🌟',
                                     min_length=1,
                                     max_length=10,
                                     required=True)
        
        self.add_item(self.button_name_input)
        self.add_item(self.emoji_input)

    async def on_submit(self, interaction):
        button_name = self.button_name_input.value
        emoji = self.emoji_input.value
        embed_cog = self.bot.get_cog("CreateEmbed")
        role_name = self.role.name
        role_id = self.role.id
        try:
            database_cog = self.bot.get_cog("Database")
            await database_cog.handle_server_role(interaction.guild.id, "set", button_name, role_name, role_id, emoji)
            
            embed = await embed_cog.create_embed(title="Success", description=f"Role and button mapping for '{button_name}' added successfully!", color=Colour.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = await embed_cog.create_embed(title="Error", description=f"Error adding role and button mapping: {e}", color=Colour.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

class RoleSelect(Select):
    def __init__(self, bot, roles: list[discord.Role]):
        self.bot = bot
        # Ensure the options don't exceed the limit Discord allows (25)
        options = [discord.SelectOption(label=role.name, value=str(role.id)) for role in roles][:25]

        super().__init__(
            placeholder="Choose a role to create button...",
            min_values=1,  # Minimum number of values that must be selected
            max_values=1,  # Maximum number of values that can be selected
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # Get the role ID from the selected option
        role_id = int(self.values[0])
        role = discord.utils.get(interaction.guild.roles, id=role_id)

        if role:
            modal = RoleMappingModal(self.bot, guild=interaction.guild, role=role)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("Role not found.", ephemeral=True)


class MapChannelSelect(Select):
    def __init__(self, bot, guild):
        self.bot = bot
        self.guild = guild
        channels = guild.text_channels
        options = [discord.SelectOption(label=channel.name, value=str(channel.id)) for channel in channels][:25]
        super().__init__(
            placeholder="Choose a channel to create button...",
            min_values=1,  # Minimum number of values that must be selected
            max_values=1,  # Maximum number of values that can be selected
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_channel_id = int(self.values[0])
        selected_channel = self.guild.get_channel(selected_channel_id)
        
        if selected_channel:
            modal = MapChannelModal(self.bot, guild=self.guild, channel=selected_channel)
            await interaction.response.send_modal(modal)


class MapChannelModal(Modal):
    def __init__(self, bot, guild, channel):
        super().__init__(title="Channel Configuration")
        self.bot = bot
        self.channel = channel
        
        self.display_name_input = TextInput(label='Enter Display Name',
                                            style=discord.TextStyle.short,
                                            placeholder=f'Display name you want to call this channel\n\nExample: Welcome Channel',
                                            min_length=1,
                                            max_length=45,
                                            required=True)
        
        self.add_item(self.display_name_input)

    async def on_submit(self, interaction):
        display_name = self.display_name_input.value
        embed_cog = self.bot.get_cog("CreateEmbed")
        channel_name = self.channel.name
        channel_id = self.channel.id
        try:
            database_cog = self.bot.get_cog("Database")
            await database_cog.handle_channel(interaction.guild.id, "set_mapping", display_name, channel_name, int(channel_id), None, None)
            embed = await embed_cog.create_embed(title="Success", 
                                                 description=f"Channel '{display_name}' set successfully. You can now use this channel name in /setup commands.", 
                                                 color=Colour.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = await embed_cog.create_embed(title="Error", description=f"Error setting channel: {e}", color=Colour.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)


class SetupCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.get_cog("Database") 

    @app_commands.command(name='setup', description='Press ENTER to choose a sub-command.')
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction):
        embed_cog = self.bot.get_cog("CreateEmbed")
        # Create the embed
        embed = await embed_cog.create_embed(title="Setup Command",
                                             description="Select a Setup Sub-Command below:",
                                             color=discord.Colour.blue())
        commands = ["Map Roles and Create Buttons", "Map Channel Names to Database", "Welcome Page Setup", 
                    "Support Ticket Setup", "Add FAQ", "Remove FAQ", "Retroactively Add XP"]
        select = SetupSelect(self.bot, custom_id="setup_command", placeholder="Select a Command")
        select.options = [discord.SelectOption(label=command, value=command) for command in commands]
        view = discord.ui.View()
        view.add_item(select)
        # Send the embed and the select menu view in the same message
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ChannelSelect(Select):
    def __init__(self, bot, db_cog, guild_id, channel_type):
        super().__init__(placeholder='Choose a channel')
        self.bot = bot
        self.db_cog = db_cog
        self.guild_id = guild_id
        self.channel_type = channel_type
        self.options = []

    async def set_options_from_db(self):
        # Get channel info from the new Database cog's method
        channel_info = await self.db_cog.handle_channel(self.guild_id, "get_channel_info")
        # Populate the dropdown options
        self.options = [discord.SelectOption(label=name, value=json.dumps({"name": name, "id": channel_id})) for name, channel_id in channel_info]

    async def callback(self, interaction):
        selected_channel_data = json.loads(self.values[0])
        selected_channel_display_name = selected_channel_data["name"]
        selected_channel_id = selected_channel_data["id"]
        
        guild_id = interaction.guild.id
        selected_channel = discord.utils.get(interaction.guild.text_channels, id=int(selected_channel_id))
        
        welcome_cog = self.bot.get_cog('WelcomeNewUser')
        if self.channel_type == "support":
            modal = welcome_cog.SetupModal(self.bot, interaction, channel=selected_channel, modal_type="support")
        elif self.channel_type == "welcome":
            role_mapping, _ = await welcome_cog.get_role_mapping(guild_id)
            modal = welcome_cog.SetupModal(self.bot, interaction, role_mapping=role_mapping, channel=selected_channel, modal_type="welcome")
        
        await interaction.response.send_modal(modal)


async def setup(bot):
    await bot.add_cog(SetupCommand(bot))