import discord
from discord.ext import commands
from discord.ui import Button, View

class RoleButton(Button):
    def __init__(self, label, role_id, emoji=None):
        super().__init__(label=label, custom_id=role_id, emoji=emoji)
        self.role_id = role_id

    async def callback(self, interaction):
        role = interaction.guild.get_role(int(self.role_id))
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"Removed {self.label} role!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"Added {self.label} role!", ephemeral=True)

class RulesView(View):
    def __init__(self, db, guild_id):
        super().__init__(timeout=None)
        
        role_mapping = {
            "Read the Rules": "📜",
            "Patreon Announcements": "🎉",
            "Announcements": "📢",
            "Behind the Scenes": "🎥",
            "Showcase": "🖼"
        }

        for role_name, emoji in role_mapping.items():
            role_id = db.get_server_role(guild_id, role_name)
            if role_id:  # Only add the button if the role_id exists in the database
                self.add_item(RoleButton(label=role_name, role_id=role_id, emoji=emoji))

class WelcomeNewUser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Get the default channel
        default_channel = member.guild.system_channel
        if not default_channel:
            # If the system channel isn't set, try to get the first channel the bot can send messages to
            default_channel = next((c for c in member.guild.text_channels if c.permissions_for(member.guild.me).send_messages), None)
        
        if not default_channel:
            return  # No channel found to send the message

        embed = discord.Embed(title="Welcome to our server!", description="Here are the rules...")
        view = RulesView(self.bot.db, member.guild.id)

        # Send the message in the default channel as an ephemeral message
        await default_channel.send(content=f"Welcome {member.mention}!", embed=embed, view=view, ephemeral=True)


def setup(bot):
    bot.add_cog(WelcomeNewUser(bot))
