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

            select_menu = Support.UpscaleSelect(self.bot, interaction)
            view = discord.ui.View()
            view.add_item(select_menu)
            embed = discord.Embed(title="Support Ticket", description="Please choose the type of ticket you'd like to create:", color=Colour.green())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        

        @discord.ui.button(style=ButtonStyle.success, label="Report A User", custom_id="report", row=1)
        async def report(self, interaction, button):
            modal = Support.ReportModal(self.bot, interaction, interaction.channel)
            await interaction.response.send_modal(modal=modal)

        @discord.ui.button(style=ButtonStyle.success, label="How to Use", custom_id="how_to", row=1)
        async def how_to(self, interaction, button):
            await interaction.response.defer(ephermal=True)
            # TODO: add the logic to send the user a message explaining how to use the ticket system

        @discord.ui.button(style=ButtonStyle.success, label="Commission Requests", custom_id="commission", row=2)
        async def commissions(self, interaction, button):
            await interaction.response.defer(ephemeral=True)
            await interaction.response.send_message("Report User button clicked!", ephemeral=True)
            # TODO: Send a message explaining how to use the commission system
            # Add a yes and no button so they can confirm if they want to enter a commission
            # If yes, send open a modal for them to enter the info
            # On submit of the modal, Create a private thread for the commission, 
            # If no, send a message saying they can if they change their mind

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

            super().__init__(placeholder='Choose an image to use as a reference', options=options)

        async def callback(self, interaction):
            ticket_type = self.values[0]
            match ticket_type:
                case 'mcmodels':
                    # TODO: Send an embed here explaining how mcmodels works
                    pass
                case 'patreon_model':
                    modal = Support.TicketModal(self.bot, interaction, interaction.channel, "Patreon Model")
                    await interaction.response.send_modal(modal=modal)
                case 'free_model':
                    modal = Support.TicketModal(self.bot, interaction, interaction.channel, "Free Model")
                    await interaction.response.send_modal(modal=modal)
                case 'patreon_plugins':
                    modal = Support.TicketModal(self.bot, interaction, interaction.channel, "Patreon Plugins")
                    await interaction.response.send_modal(modal=modal)
                case 'other':
                    modal = Support.TicketModal(self.bot, interaction, interaction.channel, "Other")
                    await interaction.response.send_modal(modal=modal)
                case _:
                    interaction.channel.send("Something went wrong. Please try again.", ephemeral=True)



    # Select Menu for choosing what type of free model they are opening a ticket for
    class SelectFreeModel(Select):
        def __init__(self, bot, interaction):
            self.bot = bot

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

    class TicketModal(Modal):
        def __init__(self, bot, interaction, channel, ticket_type):
            super().__init__(title=f"{ticket_type} Ticket")
            self.bot = bot
            self.channel = channel
            self.ticket_type = ticket_type
            self.product_name_input = TextInput(label='Enter product name',
                                                style=discord.TextStyle.short,
                                                placeholder='MONKEY D LUFFY! V1.0',
                                                min_length=1,
                                                max_length=100,
                                                required=True)
            self.add_item(self.product_name_input)
            self.server_version_input = TextInput(label='Enter server version',
                                                style=discord.TextStyle.short,
                                                placeholder='Paper 1.20.2 Build #241',
                                                min_length=1,
                                                max_length=20,
                                                required=True)
            self.add_item(self.server_version_input)
            self.plugin_versions_input = TextInput(label='Enter plugin versions',
                                                style=discord.TextStyle.short,
                                                placeholder='MythicMobs v5.4.1, ModelEngine v4.0.2',
                                                min_length=1,
                                                max_length=200,
                                                required=True)
            self.add_item(self.plugin_versions_input)
            self.details_input = TextInput(label=f'Enter details for {ticket_type}',
                                        style=discord.TextStyle.long,
                                        placeholder=f"""Enter your {ticket_type} issue here. 
                                        Include as much detail as possible. 
                                        You will be able to add additional images 
                                        and logs in your ticket thread.""",
                                        min_length=1,
                                        max_length=4000,
                                        required=True)
            self.add_item(self.details_input)

        async def on_submit(self, interaction):
            # Capture the input values
            product_name = self.product_name_input.value
            server_version = self.server_version_input.value
            plugin_versions = self.plugin_versions_input.value
            details = self.details_input.value

            guild = interaction.guild
            staff_channel = discord.utils.get(guild.text_channels, name='staff')

            # Notify the user that the ticket has been submitted
            await interaction.followup.send("Your ticket has been submitted.", ephemeral=True)

            # Send an embed to the staff channel
            embed = discord.Embed(title=f"New {self.ticket_type} Ticket", color=discord.Colour.blue())
            embed.add_field(name="Product Name", value=product_name, inline=False)
            embed.add_field(name="Server Version", value=server_version, inline=False)
            embed.add_field(name="Plugin Versions", value=plugin_versions, inline=False)
            embed.add_field(name="Additional Details", value=details, inline=False)

            await staff_channel.send(embed=embed)



async def setup(bot):
    await bot.add_cog(Support(bot))