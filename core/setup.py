import discord
from discord.ext import commands
from discord import app_commands, Embed, Colour
from discord.ui import Modal, TextInput, Select
from core.welcome import WelcomePageModal
import asyncio
import random

class SetupSelect(Select):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

    async def callback(self, interaction):
        selection = self.values[0]
        embed_cog = self.bot.get_cog("CreateEmbed")

        match selection:
            case "Add FAQ":
                view = AddFAQModal(self.bot)
                await interaction.response.send_modal(view)
            
            case "Remove FAQ":
                database_cog = self.bot.get_cog("Database")
                all_faqs = await database_cog.get_all_faqs(interaction.guild.id)
                faq_msg = "\n".join([f"#{faq[0]} - {faq[1]}" for faq in all_faqs])
                embed = await embed_cog.create_embed(title="FAQs", description=faq_msg, color=Colour.blue())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                select = FAQRemoveSelect(self.bot, custom_id="faq_remove_selection", placeholder="Select a FAQ to remove")
                select.options = [discord.SelectOption(label=str(faq[0]), value=str(faq[0])) for faq in all_faqs]
                view = discord.ui.View()
                view.add_item(select)
                await interaction.followup.send("Select a FAQ to remove:", view=view, ephemeral=True)
                
            case "Map Roles and Create Buttons":
                modal = RoleMappingModal(self.bot, guild=interaction.guild)
                await interaction.response.send_modal(modal)

            case "Map Channel Names to Database":
                modal = ChannelConfigModal(self.bot, guild=interaction.guild)
                await interaction.response.send_modal(modal)

            case "Welcome Page Setup":
                welcome_cog = self.bot.get_cog("WelcomeNewUser")
                role_mapping, unmapped_buttons = await welcome_cog.get_role_mapping(interaction.guild_id)
                modal = WelcomePageModal(self.bot, interaction, role_mapping)
                await interaction.response.send_modal(modal)

            case "Support Ticket Setup":
                support_cog = self.bot.get_cog("Support")
                # TODO: design the support ticket setup modal

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
                            user_data = await self.bot.get_cog('Database').get_user(message.author.id, interaction.guild.id)
                            # Check if user_data is not None before proceeding
                            if user_data is None:
                                continue
                            # Update message count
                            user_data['message_count'] += 1
                            # Add XP to the user
                            xp = random.randint(5, 50)
                            user_data['xp'] += xp
                            # Update the user data in DB
                            await self.bot.get_cog('Database').update_user(user_data, interaction.guild.id)  
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
            number = int(self.number_input.value)
            name = self.name_input.value
            content = self.content_input.value
            embed_cog = self.bot.get_cog("CreateEmbed")

            database_cog = self.bot.get_cog("Database")
            existing_faq = await database_cog.get_faq(number, interaction.guild.id)
            
            if existing_faq:
                embed = await embed_cog.create_embed(title="Error", description=f"FAQ #{number} already exists. Choose another number.", color=Colour.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            await database_cog.add_faq(number, name, content, interaction.guild.id)

            embed = await embed_cog.create_embed(title="Success", description=f"FAQ #{number} - {name} has been added successfully.", color=Colour.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            embed = await embed_cog.create_embed(title="Error", description=f"Please enter a valid number for the FAQ.", color=Colour.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = await embed_cog.create_embed(title="Error", description=f"Error adding FAQ: {e}", color=Colour.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)



class RoleMappingModal(Modal):
    def __init__(self, bot, guild):
        super().__init__(title="Map Roles and Create Buttons")
        self.bot = bot
        
        role_data = self.get_roles_formatted(guild)
        
        # Creating input fields for role and button mapping
        self.button_name_input = TextInput(label='Enter the button display name',
                                           style=discord.TextStyle.short,
                                           placeholder='Example: Patreon Support',
                                           min_length=1,
                                           max_length=100,
                                           required=True)
        self.role_name_input = TextInput(label='Enter 1 role name followed by ID',
                                         style=discord.TextStyle.long,
                                         default=f"Choose 1 delete all others:\n {role_data}",
                                         min_length=1,
                                         max_length=4000,
                                         required=True)
        self.emoji_input = TextInput(label='Enter the emoji for the button',
                                     style=discord.TextStyle.short,
                                     placeholder='Example: 🌟',
                                     min_length=1,
                                     max_length=10,
                                     required=True)
        
        self.add_item(self.button_name_input)
        self.add_item(self.role_name_input)
        self.add_item(self.emoji_input)

    @staticmethod
    def get_roles_formatted(guild):
        roles_formatted = [f"{role.name}:{role.id}" for role in guild.roles]
        return ', '.join(roles_formatted)

    async def on_submit(self, interaction):
        button_name = self.button_name_input.value
        role_input = self.role_name_input.value.split(":")
        if len(role_input) != 2:
            embed = await embed_cog.create_embed(title="Error", description="Invalid role format. Please use 'rolename:roleid'", color=Colour.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        role_name, role_id_str = role_input
        try:
            role_id = int(role_id_str)
        except ValueError:
            embed = await embed_cog.create_embed(title="Error", description="Invalid role ID format. Ensure it's a number.", color=Colour.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        emoji = self.emoji_input.value
        embed_cog = self.bot.get_cog("CreateEmbed")
        try:
            database_cog = self.bot.get_cog("Database")
            await database_cog.set_server_role(interaction.guild.id, button_name, role_name, role_id, emoji)
            
            embed = await embed_cog.create_embed(title="Success", description=f"Role and button mapping for '{button_name}' added successfully!", color=Colour.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = await embed_cog.create_embed(title="Error", description=f"Error adding role and button mapping: {e}", color=Colour.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)


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
    def __init__(self, bot, guild):
        super().__init__(title="Channel Configuration")
        self.bot = bot
        
        self.display_name_input = TextInput(label='Enter Display Name',
                                            style=discord.TextStyle.short,
                                            placeholder=f'Display name you want to call this channel\n\nExample: Welcome Channel',
                                            min_length=1,
                                            max_length=45,
                                            required=True)
        
        self.channel_name_and_id_input = TextInput(label='Enter Channel Name and ID',
                                                    style=discord.TextStyle.long,
                                                    default=f"Choose 1 delete all others\n\n{self.get_channels_formatted(guild)}",
                                                    min_length=1,
                                                    max_length=4000,
                                                    required=True)
        
        self.add_item(self.display_name_input)
        self.add_item(self.channel_name_and_id_input)

    @staticmethod
    def get_channels_formatted(guild):
        channels_formatted = [f"{channel.name}:{channel.id}" for channel in guild.channels if isinstance(channel, discord.TextChannel)]
        return ', '.join(channels_formatted)

    async def on_submit(self, interaction):
        display_name = self.display_name_input.value
        channel_data = self.channel_name_and_id_input.value.split(":")
        embed_cog = self.bot.get_cog("CreateEmbed")
        if len(channel_data) != 2:
            embed = await embed_cog.create_embed(title="Error", description="Invalid format for Channel Name and ID. Please use format: channel_name:channel_id", color=Colour.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        channel_name, channel_id = channel_data[0], channel_data[1]
        try:
            database_cog = self.bot.get_cog("Database")
            await database_cog.set_server_channel(interaction, interaction.guild.id, display_name, channel_name, int(channel_id))
            embed = await embed_cog.create_embed(title="Success", description=f"Channel '{display_name}' set successfully.", color=Colour.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = await embed_cog.create_embed(title="Error", description=f"Error setting channel: {e}", color=Colour.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

class SetupTicketSelect(Select):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        database_cog = self.bot.get_cog("Database")

    async def callback(self, interaction):
        channel = int(self.values[0])
        modal = SetupTicketModal(self.bot, interaction, channel)
        try:
            await interaction.response.send_modal(modal=modal)
        except Exception as e:
            print(f"Error: {e}")

class SetupTicketModal(Modal):
    def __init__(self, bot, interaction, channel):
        super().__init__(title="Setup Support Page")
        self.bot = bot
        self.channel = channel
        
        self.message_input = TextInput(label='Enter the support message',
                                       style=discord.TextStyle.long,
                                       placeholder='Click a button below to open a support ticket or commission request.',
                                       min_length=1,
                                       max_length=4000,
                                       required=True)
        self.add_item(self.message_input)

    async def on_submit(self, interaction):
        support_msg = self.message_input.value
        channel = self.channel_name.value
        embed_cog = self.bot.get_cog("CreateEmbed")
        database_cog = self.bot.get_cog("Database")
        await database_cog.set_channel_mapping(interaction.guild.id, channel, channel.name, channel.id, support_msg)


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


async def setup(bot):
    await bot.add_cog(SetupCommand(bot))