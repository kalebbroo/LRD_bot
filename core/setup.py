import discord
from discord.ext import commands
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
                
            case "Map Roles and Create Buttons":
                modal = RoleMappingModal(self.bot)
                await interaction.response.send_modal(modal)

            case "Map Channel Names to Database":
                view = ChannelConfigModal(self.bot)
                await interaction.response.send_modal(view)

            case "Welcome Page Setup":
                welcome_cog = self.bot.get_cog("WelcomeNewUser")
                await welcome_cog.create_welcome_page(interaction)

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


class RoleMappingModal(Modal):
    def __init__(self, bot, guild):
        super().__init__(title="Map Roles and Create Buttons")
        self.bot = bot
        
        # Fetching role information from the server
        role_names, role_ids = self.get_role_names_and_ids(guild)
        
        # Creating input fields for role and button mapping
        self.button_name_input = TextInput(label='Enter the button name',
                                           style=discord.TextStyle.short,
                                           placeholder='Example: Patreon Support',
                                           min_length=1,
                                           max_length=100,
                                           required=True)
        self.role_name_input = TextInput(label='Enter the server role name',
                                         style=discord.TextStyle.short,
                                         placeholder=f"Example roles: {role_names}",
                                         min_length=1,
                                         max_length=100,
                                         required=True)
        self.role_id_input = TextInput(label='Enter the server role ID',
                                       style=discord.TextStyle.short,
                                       placeholder=f"Example: {role_ids}",
                                       min_length=1,
                                       max_length=20,
                                       required=True)
        self.emoji_input = TextInput(label='Enter the emoji for the button',
                                     style=discord.TextStyle.short,
                                     placeholder='Example: 🌟',
                                     min_length=1,
                                     max_length=10,
                                     required=True)
        
        self.add_item(self.button_name_input)
        self.add_item(self.role_name_input)
        self.add_item(self.role_id_input)
        self.add_item(self.emoji_input)

    async def on_submit(self, interaction):
        button_name = self.button_name_input.value
        role_name = self.role_name_input.value
        role_id = int(self.role_id_input.value)
        emoji = self.emoji_input.value
        
        try:
            database_cog = self.bot.get_cog("Database")
            await database_cog.set_server_role(interaction.guild.id, button_name, role_name, role_id, emoji)
            await interaction.response.send_message(f"Role and button mapping for '{button_name}' added successfully!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error adding role and button mapping: {e}", ephemeral=True)


class ActualRoleSelect(Select):
    def __init__(self, bot, predefined_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.predefined_name = predefined_name

    async def callback(self, interaction):
        selected_server_role_id = int(self.values[0])
        role = discord.utils.get(interaction.guild.roles, id=selected_server_role_id)
        
        if role:
            try:
                database_cog = self.bot.get_cog("Database")
                await database_cog.set_server_role(interaction.guild.id, self.predefined_name, role.name, role.id)

                await interaction.response.send_message(f"Role linked to {role.name}.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"Error updating role in database: {e}", ephemeral=True)
                print(f"Error updating role in database: {e}")
        else:
            await interaction.response.send_message(f"Error: Role not found.", ephemeral=True)
            print(f"Error: Role not found.")


class ChannelConfigModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Channel Configuration")
        self.bot = bot
        
        self.display_name_input = TextInput(label='Enter Display Name',
                                            style=discord.TextStyle.short,
                                            placeholder='Enter a name you want to call this channel',
                                            min_length=1,
                                            max_length=45,
                                            required=True)
        
        self.channel_name_and_id_input = TextInput(label='Enter Channel Name and ID',
                                                   style=discord.TextStyle.short,
                                                   placeholder=f'Format: channel_name:channel_id. Example: general:1234567890',
                                                   min_length=1,
                                                   max_length=100,
                                                   required=True)
        
        self.add_item(self.display_name_input)
        self.add_item(self.channel_name_and_id_input)

    async def on_submit(self, interaction):
        display_name = self.display_name_input.value
        channel_data = self.channel_name_and_id_input.value.split(":")
        if len(channel_data) != 2:
            await interaction.response.send_message("Error: Invalid format for Channel Name and ID. Please use format: channel_name:channel_id", ephemeral=True)
            return

        channel_name, channel_id = channel_data[0], channel_data[1]
        try:
            # Using the database logic to add the channel data
            database_cog = self.bot.get_cog("Database")
            await database_cog.set_server_channel(interaction.guild.id, display_name, channel_name, int(channel_id))
            await interaction.response.send_message(f"Channel '{display_name}' set successfully.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error setting channel: {e}", ephemeral=True)
            print(f"Error setting channel: {e}")


class SetupCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.get_cog("Database") 

    @app_commands.command(name='setup', description='Press ENTER to choose a sub-command.')
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction):
        commands = ["Add FAQ", "Remove FAQ", "Map Role and Create Buttons", "Map Channel Names to Database", "Welcome Page Setup"]
        select = SetupSelect(self.bot, custom_id="setup_command", placeholder="Select a Command")
        select.options = [discord.SelectOption(label=command, value=command) for command in commands]
        view = discord.ui.View()
        view.add_item(select)
        await interaction.response.send_message("Select an Admin Command", view=view, ephemeral=True)

    async def get_role_names_and_ids(self, guild):
        roles = guild.roles
        role_names = [role.name for role in roles]
        role_ids = [f"{role.name}={role.id}" for role in roles]
        return ', '.join(role_names), ', '.join(role_ids)

async def setup(bot):
    await bot.add_cog(SetupCommand(bot))