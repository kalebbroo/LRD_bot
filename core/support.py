import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
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
        view = Support.TicketButton(self.bot, db_cog, guild_id)
        await support_channel.send(content=support_msg, view=view)


    class TicketButton(View):
        def __init__(self, bot, interaction):
            super().__init__(timeout=120)
            self.bot = bot

        @discord.ui.button(style=ButtonStyle.success, label="Create Support Ticket", custom_id="support_ticket", row=1)
        async def support_ticket(self, interaction, button):
            await interaction.response.defer(ephermal=True)
            select_menu = discord.SelectMenu(custom_id='ticket_type', placeholder='Choose a ticket type...', options=[
            discord.SelectOption(label='General Inquiry', value='general'),
            discord.SelectOption(label='Technical Issue', value='technical'),
            discord.SelectOption(label='Account Support', value='account'),
            ])
            
            action_row = discord.ActionRow(select_menu)
            
            await interaction.response.send_message("Please choose the type of ticket you'd like to create:", components=[action_row], ephemeral=True)

        @discord.ui.button(style=ButtonStyle.success, label="Report A User", custom_id="report", row=1)
        async def report(self, interaction, button):
            await interaction.response.defer(ephemeral=True)
            modal = Support.ReportModal(self.bot, interaction, interaction.channel)
            await modal.start(interaction)

        @discord.ui.button(style=ButtonStyle.success, label="How to Use", custom_id="how_to", row=1)
        async def how_to(self, interaction, button):
            await interaction.response.defer(ephermal=True)

        @discord.ui.button(style=ButtonStyle.success, label="Commission Requests", custom_id="commission", row=2)
        async def commissions(self, interaction, button):
            await interaction.response.defer(ephemeral=True)
            await interaction.response.send_message("Report User button clicked!", ephemeral=True)

    # TODO: add this logic correctly for the buttons
            
    async def ticket_type_selected(self, interaction):
        selected_value = interaction.component.selected_options[0]

        # TODO: correctly pass channel info
        
        # Create a private thread for the ticket
        guild = interaction.guild
        support_channel = self.find_channel_by_name(guild, 'support')  # Assuming you have this utility function
        staff_channel = self.find_channel_by_name(guild, 'staff')  # Assuming you have this utility function
        
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
            options = [
                discord.SelectOption(label='Pack From MCModels', value='mcmodels'),
                discord.SelectOption(label='Patreon Model', value='patreon_model'),
                discord.SelectOption(label='Free Model', value='free_model'),
                discord.SelectOption(label='Patreon Plugins', value='patreon_plugins'),
                discord.SelectOption(label='Other', value='other'),
            ]
            super().__init__(custom_id='choose_ticket', placeholder='Choose a ticket type...', options=options)

        async def callback(self, interaction):
            await interaction.response.defer()

            type_of_model_pack = self.values[0]
            select_menu = Support.SelectProduct(self.bot)
            view = discord.ui.View()
            view.add_item(select_menu)
            await interaction.channel.send("Select a product  ", view=view)


    # Select Menu for choosing what type of product they are opening a ticket for
    class SelectProduct(Select):
        def __init__(self, bot, interaction):
            self.bot = bot

            match self.values[0]:
                case 'mcmodels':
                    options = [
                        discord.SelectOption(label='Product1', value='product1'),
                        discord.SelectOption(label='Product2', value='product2'),
                    ]
                case 'patreon_model':
                    options = [
                        discord.SelectOption(label='Product1', value='product1'),
                    ]
                case 'free_model':
                    options = [
                        discord.SelectOption(label='Product1', value='product1'),
                    ]
                case 'patreon_plugins':
                    options = [
                        discord.SelectOption(label='Product1', value='product1'),
                    ]
                case 'other':
                    options = [
                        discord.SelectOption(label='Product1', value='product1'),
                    ]
                case _:
                    interaction.channel.send("Something went wrong. Please try again.", ephemeral=True)


            super().__init__(custom_id='select_product', placeholder='Choose a product...', options=options)

        async def callback(self, bot, interaction):
            await interaction.response.defer()

            specific_product = self.values[0]
            # TODO: add the logic to create ticket in a private thread
            await self.ticket_type_selected(self, interaction)


    class ReportModal(Modal):
        def __init__(self, bot, interaction, channel):
            super().__init__(title="Report a User")
            self.bot = bot
            self.channel = channel
            
            self.user_id_input = TextInput(label='Enter the User ID to report',
                                        style=discord.TextStyle.short,
                                        placeholder='Enter User ID',
                                        min_length=1,
                                        max_length=20,
                                        required=True)
            self.add_item(self.user_id_input)
            self.reason_input = TextInput(label='Enter the reason for reporting',
                                        style=discord.TextStyle.long,
                                        placeholder='Enter your reason here',
                                        min_length=1,
                                        max_length=4000,
                                        required=True)
            self.add_item(self.reason_input)

        async def on_submit(self, interaction):
            reported_user_id = self.user_id_input.value
            reason = self.reason_input.value
            guild = interaction.guild
            staff_channel = discord.utils.get(guild.text_channels, name='staff')
            
            # Validate that the user ID exists in the server
            reported_user = guild.get_member(int(reported_user_id))
            if not reported_user:
                await interaction.followup.send("The user ID provided does not belong to this server.", ephemeral=True)
                return
            # Notify the user that the report has been submitted
            await interaction.followup.send("Your report has been submitted.", ephemeral=True)
            
            # Send an embed to the staff channel
            embed = discord.Embed(title="New User Report", color=discord.Colour.red())
            embed.add_field(name="Reported User ID", value=reported_user_id, inline=False)
            embed.add_field(name="Reason for Report", value=reason, inline=False)
            
            await staff_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Support(bot))