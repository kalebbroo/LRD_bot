import discord
from discord.ext import commands
from discord.ui import View, Button, Select
from discord import ButtonStyle, Interaction, ui
from discord import Colour
from datetime import datetime, timedelta

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO: create a template the user has to follow when creating a ticket
    # TODO: create a ticket system for free items
    # TODO: create a ticket system for patreon items
    # TODO: send users to correct location for mcmodels
    # TODO: send users to correct location for commissions

    """Redundency check for the support buttons. Will refresh the support message if the bot is restarted."""

    async def refresh_support_message(self, guild_id):
        db_cog = self.bot.get_cog("Database")
        support_channel_name = await db_cog.get_support_channel(guild_id)
        support_msg = await db_cog.get_support_message(guild_id)
        guild = self.bot.get_guild(guild_id)

        if not support_channel_name:
            print(f"No welcome channel set for {guild.name}. Skipping welcome message refresh.")
            return
        
        if not support_msg or support_msg.strip() == "":
            print(f"No welcome message set for {guild.name}. Skipping welcome message send.")
            return
        
        support_channel = discord.utils.get(guild.text_channels, name=support_channel_name)
        if not support_channel:
            print(f"No channel named {support_channel_name} found in {guild.name}")
            return
        
        # Delete the last message in the welcome channel
        try:
            last_message = await support_channel.fetch_message(support_channel.last_message_id)
            if last_message.author == self.bot.user:  # Ensure the last message was sent by the bot
                await last_message.delete()
        except Exception as e:
            print(f"Error deleting the support message: {e}")

        # Repost the welcome message with the buttons
        role_mapping, _ = await self.get_role_mapping(guild_id)
        view = Support.SupportView(self.bot, db_cog, guild_id, role_mapping)
        await support_channel.send(content=support_msg, view=view)

    class SupportView(View):
        def __init__(self, bot, database_cog, guild_id, role_mapping):
            super().__init__(timeout=None)
            self.database = database_cog
            self.bot = bot

            for button_name, role_info in role_mapping.items():
                #print(f"Adding button: {button_name}, Role ID: {role_info['role_id']}, Emoji: {role_info['emoji']}")
                # Pass the bot instance when creating the RoleButton
                self.add_item(Support.TicketButton(self.bot, label=button_name, role_id=role_info['role_id'], emoji=role_info['emoji']))

    class TicketButton(Button):
        cooldown_users = {}

        def __init__(self, bot, label, role_id, emoji=None):
            super().__init__(label=label, custom_id=str(role_id), emoji=emoji)
            self.bot = bot
            self.role_id = role_id

        @discord.ui.button(style=ButtonStyle.success, label="Create Support Ticket", custom_id="support_ticket", row=1)
        async def regenerate(self, interaction, button):
            await interaction.response.defer(ephermal=True)
            select_menu = discord.SelectMenu(custom_id='ticket_type', placeholder='Choose a ticket type...', options=[
            discord.SelectOption(label='General Inquiry', value='general'),
            discord.SelectOption(label='Technical Issue', value='technical'),
            discord.SelectOption(label='Account Support', value='account'),
            ])
            
            action_row = discord.ActionRow(select_menu)
            
            await interaction.response.send_message("Please choose the type of ticket you'd like to create:", components=[action_row], ephemeral=True)

        @discord.ui.button(style=ButtonStyle.success, label="Report A User", custom_id="report", row=1)
        async def regenerate(self, interaction, button):
            await interaction.response.defer(ephermal=True)
            await interaction.response.send_message("Report User button clicked!", ephemeral=True)

        @discord.ui.button(style=ButtonStyle.success, label="How to Use", custom_id="how_to", row=1)
        async def regenerate(self, interaction, button):
            await interaction.response.defer(ephermal=True)

        @discord.ui.button(style=ButtonStyle.success, label="Commission Requests", custom_id="commission", row=2)
        async def regenerate(self, interaction, button):
            await interaction.response.defer(ephemeral=True)
            await interaction.response.send_message("Report User button clicked!", ephemeral=True)

    # TODO: add this logic correctly for the buttons
            
    async def ticket_type_selected(self, interaction):
        selected_value = interaction.component.selected_options[0]

        # TODO: correctly pass channel info
        
        # Create a private thread for the ticket
        guild = discord.utils.get(self.bot.guilds)
        staff_channel = discord.utils.get(guild.text_channels, name='staff')
        support_channel = discord.utils.get(guild.text_channels, name='support')
        
        thread = await support_channel.create_text_channel(f"{selected_value}-ticket")
        
        # Create a "Join Ticket" button
        join_ticket_button = discord.Button(style=discord.ButtonStyle.primary, label="Join Ticket")
        
        # Create an action row
        action_row = discord.ActionRow(join_ticket_button)
        
        # Send a message to the staff channel
        await staff_channel.send(f"A new {selected_value} ticket has been created!", components=[action_row])
        
        await interaction.response.send_message(f"You selected: {selected_value}. A new ticket thread has been created.", ephemeral=True)

    # TODO: Add select menu logic


    # Select Menu for choosing what type of ticket they are opening
    class ChooseTicket(Select):
        def __init__(self, bot):
            self.bot = bot

            # TODO: add the choices for what type of models they are opening a ticket for

        async def callback(self, interaction):
            await interaction.response.defer()

            type_of_model_pack = self.values[0]
            select_menu = Support.SelectProduct(self.bot)
            view = discord.ui.View()
            view.add_item(select_menu)
            await interaction.channel.send("Select a product  ", view=view)


    # Select Menu for choosing what type of product they are opening a ticket for
    class SelectProduct(Select):
        def __init__(self, bot):
            self.bot = bot

            # TODO: add the choices for specific products

        async def callback(self, interaction):
            await interaction.response.defer()

            specific_product = self.values[0]
            # TODO: add the logic to create ticket in a private thread
            await self.ticket_type_selected(self, interaction)

async def setup(bot):
    await bot.add_cog(Support(bot))