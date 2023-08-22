import discord
from discord.ext import commands
from discord.ui import Button, View

class RoleButton(Button):
    def __init__(self, label, role_id, emoji=None):
        super().__init__(label=label, custom_id=role_id, emoji=emoji)
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(int(self.role_id))
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"Removed {self.label} role!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"Added {self.label} role!", ephemeral=True)

class RulesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # Add roles buttons
        # (You can replace 'ROLE_ID' with the actual role ID for each role)
        self.add_item(RoleButton(label="Read the Rules", role_id="ROLE_ID1", emoji="📜"))
        self.add_item(RoleButton(label="Patreon Announcements", role_id="ROLE_ID2", emoji="🎉"))
        self.add_item(RoleButton(label="Announcements", role_id="ROLE_ID3", emoji="📢"))
        self.add_item(RoleButton(label="Behind the Scenes", role_id="ROLE_ID4", emoji="🎥"))
        self.add_item(RoleButton(label="Showcase", role_id="ROLE_ID5", emoji="🖼"))

class WelcomeNewUser(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Send a private message to the new user
        embed = discord.Embed(title="Welcome to our server!", description="Here are the rules...")
        view = RulesView()
        await member.send(embed=embed, view=view)

    @commands.command(name='setRules')
    @commands.has_permissions(administrator=True)
    async def set_rules(self, interaction: discord.Interaction):
        # Send the rules in the desired channel with the role buttons
        embed = discord.Embed(title="Server Rules", description="Please select your roles below.")
        view = RulesView()
        await interaction.response.send_message(embed=embed, view=view)

def setup(bot):
    bot.add_cog(WelcomeNewUser(bot))
