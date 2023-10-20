import discord
from discord.ext import commands
from discord.ui import View, Button, Select, Modal, TextInput
from discord import ButtonStyle, Interaction, ui
from discord import Colour
from datetime import datetime, timedelta

class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_cog = bot.get_cog("CreateEmbed")

    """Redundency check for the support buttons. Will refresh the support message if the bot is restarted."""

    async def refresh_support_message(self, guild_id):
        db_cog = self.bot.get_cog("Database")
        create_embed_cog = self.bot.get_cog("CreateEmbed")
        support_channel_name = await db_cog.get_support_channel(guild_id)
        support_msg = await db_cog.get_support_message(guild_id, support_channel_name)
        guild = self.bot.get_guild(guild_id)
        print(f"Refreshing support message for {guild.name}.\n")
        print(f"Support channel name: {support_channel_name}\n")
        print(f"Support message: {support_msg}\n")
        
        if not support_channel_name:
            print(f"No support channel set for {guild.name}. Skipping support message refresh.")
            return
        
        if not support_msg or support_msg.strip() == "":
            print(f"No support message set for {guild.name}. Skipping support message send.")
            return
        
        # Fetch the channel ID from the database based on the channel's display name
        support_channel_id = await db_cog.get_id_from_display(guild_id, support_channel_name)
        support_channel = self.bot.get_channel(support_channel_id)
        
        if not support_channel:
            print(f"No channel with ID {support_channel_id} found in {guild.name}")
            return
        
        # Create the embed
        embed = await create_embed_cog.create_embed(
            title="Support Channel Information",
            description=support_msg,
            color=discord.Colour.blue()
        )
        # Delete the last message in the support channel
        try:
            last_message = await support_channel.fetch_message(support_channel.last_message_id)
            if last_message.author == self.bot.user:  # Ensure the last message was sent by the bot
                await last_message.delete()
        except Exception as e:
            print(f"Error deleting the support message: {e}")
        
        # Repost the support message with the buttons
        view = Support.TicketButton(self.bot, None)
        await support_channel.send(embed=embed, view=view)



    class TicketButton(View):
        def __init__(self, bot, interaction):
            super().__init__(timeout=None)
            self.bot = bot

        @discord.ui.button(style=ButtonStyle.success, label="Create Support Ticket", custom_id="support_ticket", row=1)
        async def support_ticket(self, interaction, button):

            select_menu = Support.ChooseTicket(self.bot, interaction)
            view = discord.ui.View()
            view.add_item(select_menu)
            embed = discord.Embed(title="Support Ticket", description="Please choose the type of ticket you'd like to create:", color=Colour.green())
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        

        @discord.ui.button(style=ButtonStyle.danger, label="Report A User", custom_id="report", row=1)
        async def report(self, interaction, button):
            modal = Support.ReportModal(self.bot, interaction, interaction.channel)
            await interaction.response.send_modal(modal)

        @discord.ui.button(style=ButtonStyle.secondary, label="How to Use", custom_id="how_to", row=1)
        async def how_to(self, interaction, button):
            # Use CreateEmbed cog to make an embed
            embed = await self.bot.get_cog("CreateEmbed").create_embed(
                title="How to Use the Support Ticket System",
                description="Here's how to use the support ticket system.",
                color=discord.Colour.blue(),
                fields=[
                    ("Create Support Ticket", "Click this button to create a new support ticket. You'll be presented with options to specify the type of your ticket.", False),
                    ("Report A User", "Click this button if you want to report a user. A form will appear asking for details.", False),
                    ("Commission Requests", "Click this button for commission related queries. You'll be guided through the process.", False)
                ]
            )
            # Send the embed
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @discord.ui.button(style=ButtonStyle.primary, label="Commission Requests", custom_id="commission", row=2)
        async def commissions(self, interaction, button):
            await interaction.response.defer(ephemeral=True)
            commissions = self.bot.get_cog("Commissions")
            
            # Create an embed to explain the commission system in detail
            embed = await self.bot.get_cog("CreateEmbed").create_embed(
                title="Commission Requests",
                description="Heyo! Commissions are finally open, here's how this will work.",
                color=discord.Colour.green(),
                fields=[
                    ("How to Start", "Just shoot me a DM with as much information about your Mob as you can (skills, behavior, etc). Reference photos are appreciated!", False),
                    ("Payment", "First half of payment on start of work and second half when completed.", False),
                    ("Reworks", "The first two reworks are free but after that it's $10.", False),
                    ("Pricing", "Custom Mob -\nModel & Texture - $125 USD\nAnimation - $20 USD (each)\nMythicmobs Configuration - $125 USD", False),
                    ("Extras", "Custom Sound Effects - $30 USD\nItems - $15 USD (each)\nHigh-res Render - $50 USD", False),
                    ("Note", "This is a baseline price-point. If you have a grand concept with a ton of skills, the price may vary.", False)
                ]
            )
            
            view = commissions.CommissionView(self.bot)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

            # TODO: Send a message explaining how to use the commission system
            # Add a yes and no button so they can confirm if they want to enter a commission
            # If yes, send open a modal for them to enter the info
            # On submit of the modal, Create a private thread for the commission, 
            # If no, send a message saying they can if they change their mind


    # Select Menu for choosing what type of ticket they are opening
    class ChooseTicket(Select):
        def __init__(self, bot, interaction):
            self.bot = bot
            self.interaction = interaction

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
            guild = interaction.guild
            member = guild.get_member(interaction.user.id)
            allowed_roles = ["Golem", "Gold Golem", "Shaman", "Hermitcrab"]
            has_allowed_role = any(role.name in allowed_roles for role in member.roles)

            match ticket_type:
                case 'mcmodels':
                    embed_cog = self.bot.get_cog("CreateEmbed")
                    embed = await embed_cog.create_embed(
                        title="MC-Models Content Support",
                        description="We provide support for MC-Models packs exclusively on the MC-Models Discord.",
                        color=discord.Colour.green(),
                        fields=[
                            ("How to Get Support", "Please open a ticket on the MC-Models Discord with your order number and we will be with you ASAP.", False),
                            ("Discord Invite", "[Join MC-Models Discord](https://discord.com/invite/MCModels)", False),
                            ("Perks", "Private channels so we can share: logs, configs, even files, without risking leaks on either end.", False),
                            ("Order Verification", "The bot tracks and checks order numbers to verify purchases.", False),
                            ("Message Tracking", "Your issue won't get lost or buried when other people post messages.", False)
                        ]
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                case 'patreon_model':
                    if not has_allowed_role:
                        await self.send_patreon_info(interaction)
                    else:
                        modal = Support.TicketModal(self.bot, interaction, interaction.channel, "Patreon Model")
                        await interaction.response.send_modal(modal)
                case 'patreon_plugins':
                    if not has_allowed_role:
                        await self.send_patreon_info(interaction)
                    else:
                        modal = Support.TicketModal(self.bot, interaction, interaction.channel, "Patreon Plugins")
                        await interaction.response.send_modal(modal)
                case 'free_model':
                    modal = Support.TicketModal(self.bot, interaction, interaction.channel, "Free Model")
                    await interaction.response.send_modal(modal)
                case 'other':
                    modal = Support.TicketModal(self.bot, interaction, interaction.channel, "Other")
                    await interaction.response.send_modal(modal)
                case _:
                    await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)

        async def send_patreon_info(self, interaction):
            embed_cog = self.bot.get_cog("CreateEmbed")
            embed = await embed_cog.create_embed(
                title="Patreon Information",
                description="Here's how to get access to Patreon roles and content.",
                color=discord.Colour.red(),
                fields=[
                    ("Billing Information", "Patreon billing is a bit tricky, and you may experience issues like double billing. For more details, [click here](https://tinyurl.com/LittleRoomDevFAQ-06).", False),
                    ("What's Available on Patreon?", "Different tiers provide access to different types of content. For a complete rundown, [click here](https://tinyurl.com/LittleRoomDevFAQ-07-1) and [here](https://tinyurl.com/LittleRoomDevFAQ-07-2).", False),
                    ("Getting Support and Roles", "To get your Discord role and to access support, link your Discord to your Patreon account. For more information, [click here](https://tinyurl.com/LittleRoomDevFAQ-08).", False)
                ]
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


    class ReportModal(Modal):
        def __init__(self, bot, interaction, channel):
            super().__init__(title="Report a User")
            self.bot = bot
            self.channel = channel
            self.guild_id = interaction.guild.id 
            
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
            # Get the Database cog
            db_cog = self.bot.get_cog("Database")
            # Fetch all display names from the database
            all_display_names = await db_cog.get_channel_display_names(self.guild_id)
            # Find the first display name that contains 'admin' or 'staff'
            staff_channel_name = next((name for name in all_display_names if 'admin' in name.lower() or 'staff' in name.lower()), None)
            
            if staff_channel_name:
                # Fetch the corresponding channel ID from the database
                staff_channel_id = await db_cog.get_id_from_display(self.guild_id, staff_channel_name)
                staff_channel = self.bot.get_channel(staff_channel_id)
            else:
                await interaction.followup.send("No admin or staff channel found.", ephemeral=True)
                return

            # Get the reported user ID and reason for the report
            reported_user_id = self.user_id_input.value
            reason = self.reason_input.value

            # Get the guild and validate that the user ID exists in the server
            guild = interaction.guild
            reported_user = guild.get_member(int(reported_user_id))
            if not reported_user:
                await interaction.followup.send("The user ID provided does not belong to this server.", ephemeral=True)
                return
                
            # Notify the user that the report has been submitted
            await interaction.followup.send("Your report has been submitted.", ephemeral=True)

            # Create the embed
            embed = await self.bot.get_cog("CreateEmbed").create_embed(
                title="New User Report",
                color=discord.Colour.red(),
                fields=[
                    ("Reported User ID", reported_user_id, False),
                    ("Reason for Report", reason, False)
                ]
            )
            # Send the embed to the staff channel
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
                                        Include as much detail as possible.""",
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

            db_cog = self.bot.get_cog("Database")
            all_display_names = await db_cog.get_channel_display_names(interaction.guild.id)
            staff_channel_name = next((name for name in all_display_names if 'admin' in name.lower() or 'staff' in name.lower()), None)
            
            if staff_channel_name:
                staff_channel_id = await db_cog.get_id_from_display(interaction.guild.id, staff_channel_name)
                staff_channel = self.bot.get_channel(staff_channel_id)
            else:
                await interaction.followup.send("No admin or staff channel found.", ephemeral=True)
                return
            
            # Create a private thread for the ticket
            thread = await staff_channel.create_text_channel(
                name=f"{self.ticket_type}-ticket-{interaction.user.name}",
                type=discord.ChannelType.private_thread
            )

            # Notify the user that the ticket has been submitted
            await interaction.followup.send("Your ticket has been submitted.", ephemeral=True)

            # Send an embed to the thread with the provided details
            embed = await self.bot.get_cog("CreateEmbed").create_embed(
                title=f"New {self.ticket_type} Ticket",
                color=discord.Colour.blue(),
                fields=[
                    ("Product Name", product_name, False),
                    ("Server Version", server_version, False),
                    ("Plugin Versions", plugin_versions, False),
                    ("Additional Details", details, False)
                ]
            )
            await thread.send(embed=embed)
            # Notify the user that they can upload any additional images or logs in the thread
            await thread.send(f"{interaction.user.mention}, you can upload any images or logs needed here.")

    class SupportMessageModal(Modal):
        def __init__(self, bot, guild_id, channel_display_name):
            super().__init__(title="Enter Support Message")
            self.bot = bot
            self.guild_id = guild_id
            self.channel_display_name = channel_display_name

            self.message_input = TextInput(
                label='Message to explain support tickets',
                style=discord.TextStyle.long,
                placeholder='Enter the info message to show in the support channel. The ticket buttons will be added below it.',
                min_length=1,
                max_length=4000,
                required=True
            )
            self.add_item(self.message_input)

        async def on_submit(self, interaction):
            await interaction.response.defer(ephemeral=True)
            support_msg = self.message_input.value
            db_cog = self.bot.get_cog("Database")
            channel_id = await db_cog.get_id_from_display(self.guild_id, self.channel_display_name)
            channel = self.bot.get_channel(channel_id)
            print(f"Updating the message for {self.channel_display_name} in {channel.name}.")

            # Update the message in the database
            update_success = await db_cog.update_channel_message(self.guild_id, self.channel_display_name, support_msg)
            if update_success:
                print(f"Successfully updated the message for {self.channel_display_name} in the database.")
            else:
                print(f"Failed to update the message for {self.channel_display_name} in the database.")

            # Create the view with buttons for the support ticket system
            view = Support.TicketButton(self.bot, interaction)
            
            # Post the message with the buttons in the support channel
            await channel.send(content=support_msg, view=view)




async def setup(bot):
    await bot.add_cog(Support(bot))