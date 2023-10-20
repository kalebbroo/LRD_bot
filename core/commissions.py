import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from discord import ButtonStyle, Interaction, ui


class Commissions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_cog = bot.get_cog("CreateEmbed")

    class CommissionView(View):
        def __init__(self, bot):
            super().__init__(timeout=None)
            self.bot = bot

        @discord.ui.button(style=ButtonStyle.success, label="Yes", custom_id="commission_yes", row=1)
        async def commission_yes(self, interaction: Interaction, button: Button):
            # Open a modal for the user to enter commission info
            modal = Commissions.CommissionModal(self.bot)
            await interaction.response.send_modal(modal)

        @discord.ui.button(style=ButtonStyle.danger, label="No", custom_id="commission_no", row=1)
        async def commission_no(self, interaction: Interaction, button: Button):
            # Send a message saying they can if they change their mind
            await interaction.response.send_message("You can always decide to enter a commission later if you change your mind.", ephemeral=True)

    class CommissionModal(Modal):
        def __init__(self, bot):
            super().__init__(title="Commission Request")
            self.bot = bot
            
            # Text input for the type of mob
            self.comission_type = TextInput(
                label="Type of Commission",
                style=discord.TextStyle.short,
                placeholder="Mob, Item, etc.",
                min_length=1,
                max_length=100,
                required=True
            )
            self.add_item(self.comission_type)
            
            # Text input for skills and behavior
            self.description = TextInput(
                label="Description of the Commission",
                style=discord.TextStyle.long,
                placeholder="""Describe in detail the commission and be sure to include your budget. 
                We can normally work with budgets of all sizes. 
                However LRD is not interested in trading work for exposure.""",
                min_length=1,
                max_length=4000,
                required=True
            )
            self.add_item(self.description)
            
            # Text input for any extras
            self.extras = TextInput(
                label="Extras (Sound Effects, Items, etc.)",
                style=discord.TextStyle.short,
                placeholder="Enter any extras you'd like",
                min_length=1,
                max_length=200,
                required=False
            )
            self.add_item(self.extras)
            
        async def on_submit(self, interaction):
            # Capture the input values
            type = self.comission_type.value
            description = self.description.value
            extras = self.extras.value if self.extras.value else "None"

            guild = interaction.guild
            staff_channel = discord.utils.get(guild.text_channels, name='staff')
            
            # Create a private thread for the commission
            thread = await staff_channel.create_text_channel(
                name=f"commission-{interaction.user.name}",
                type=discord.ChannelType.private_thread
            )
            # Notify the user that the commission has been submitted
            await interaction.followup.send("Your commission request has been submitted.", ephemeral=True)

            # Send an embed to the thread with the provided details
            embed = await self.bot.get_cog("CreateEmbed").create_embed(
                title="New Commission Request",
                color=discord.Colour.blue(),
                fields=[
                    ("Mob Type", type, False),
                    ("Skills and Behavior", description, False),
                    ("Extras", extras, False)
                ]
            )
            await thread.send(embed=embed)
            
            # Notify the user that they can upload any additional images or logs needed here
            await thread.send(f"{interaction.user.mention}, you can submit more info here if you'd like, including reference pictures.")



async def setup(bot):
    await bot.add_cog(Commissions(bot))