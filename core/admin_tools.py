from discord.ext.commands import BucketType, cooldown
from discord import app_commands, Embed, Colour
from datetime import datetime, timedelta
from discord.ext import commands
from discord.utils import get
import discord

class AdminControls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.get_cog("Database")

    async def cog_check(self, ctx):
        """Check if the command invoker has admin permissions."""
        return ctx.author.guild_permissions.administrator
    
    def is_new_member(self, member):
        """Check if a member is new to the guild."""
        naive_utc_now = datetime.utcnow().replace(tzinfo=None)
        return naive_utc_now - member.joined_at.replace(tzinfo=None) < timedelta(days=7)



    @app_commands.command(name='mute', description='Mute a member')
    @app_commands.describe(user='The member to mute', reason='The reason for the mute')
    async def mute(self, interaction, user: discord.Member, reason: str):
        """Mute a member in the server."""
        await interaction.response.defer()
        try:
            role = get(interaction.guild.roles, name="Muted")
            if not role:
                role = await interaction.guild.create_role(name="Muted")
                for channel in interaction.guild.channels:
                    await channel.set_permissions(role, speak=False, send_messages=False)
            await user.add_roles(role, reason=reason)
            embed = Embed(title="Mute", description=f"{user.mention} has been muted.", color=Colour.red())
            if reason:
                embed.add_field(name="Reason", value=reason)
            await interaction.followup.send(embed=embed)
            await self.add_moderation_log(interaction.guild.id, "mute", user.id, interaction.user.id, reason, datetime.utcnow().timestamp())
        except Exception as e:
            await interaction.channel.send(f"An error occurred: {e}", ephemeral=True)
            print(f"An error occurred: {e}")


    @app_commands.command(name='unmute', description='Unmute a member')
    @app_commands.describe(user='The member to mute')
    async def unmute(self, interaction, user: discord.Member):
        await interaction.response.defer()
        try:
            role = get(interaction.guild.roles, name="Muted")
            if role in user.roles:
                await user.remove_roles(role)
                embed = Embed(title="Unmute", description=f"{user.mention} has been unmuted.", color=Colour.green())
                await interaction.followup.send(embed=embed)
            else:
                await interaction.channel.send(f"{user.mention} is not muted.", ephemeral=True)
        except Exception as e:
            await interaction.channel.send(f"An error occurred: {e}", ephemeral=True)
            print(f"An error occurred: {e}")


    @app_commands.command(name='kick', description='Kick a member from the server')
    @app_commands.describe(user='The member to kick', reason='The reason for the kick')
    async def kick(self, interaction, user: discord.Member, reason: str):
        """Kick a member from the server."""
        try:
            await interaction.response.defer()
            await user.kick(reason=reason)
            await interaction.followup.send(f"{user.mention} has been kicked for {reason}.")
            await self.db.add_moderation_log(interaction.guild.id, "kick", user.id, interaction.user.id, reason, datetime.utcnow().timestamp())
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)
            print(f"An error occurred: {e}")


    @app_commands.command(name='ban', description='Ban a member from the server')
    @app_commands.describe(user='The member to ban', reason='The reason for the ban')
    async def ban(self, interaction, user: discord.Member, reason: str):
        """Ban a member from the server."""
        try:
            await interaction.response.defer()
            await user.ban(reason=reason)
            await interaction.followup.send(f"{user.mention} has been banned for {reason}.")
            await self.db.add_moderation_log(interaction.guild.id, "ban", user.id, interaction.user.id, reason, datetime.utcnow().timestamp())
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)
            print(f"An error occurred: {e}")


    @app_commands.command(name='adjust_roles', description='Add or remove a user\'s role')
    @app_commands.describe(user='The user to adjust the role of', action='The action to perform (add or remove)')
    async def adjust_roles(self, interaction, user: discord.Member, action: str):
        await interaction.response.defer()
        try:
            if action.lower() == 'add':
                roles = [role for role in interaction.guild.roles if role != interaction.guild.default_role]
                select = RoleSelect(placeholder='Select a role to add', roles=roles, action='add')
            elif action.lower() == 'remove':
                roles = [role for role in user.roles if role != interaction.guild.default_role]
                select = RoleSelect(placeholder='Select a role to remove', roles=roles, action='remove')
            else:
                await interaction.followup.send("Invalid action. Please enter 'add' or 'remove'.")
                return

            view = discord.ui.View()
            view.add_item(select)
            await interaction.followup.send(f"Please select a role to {action} for {user.mention}:", view=view)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)
            print(f"An error occurred: {e}")


    @app_commands.command(name='announcement', description='Send an announcement message to all users')
    @app_commands.describe(message='The message to send to all users')
    @app_commands.checks.has_permissions(administrator=True)
    async def send_message(self, interaction, *, message: str = None):
        await interaction.response.defer()
        for member in interaction.guild.members:
            if not member.bot:
                await member.send(message)


    @commands.Cog.listener()
    async def on_channel_create(self, channel):
        """Ensure the Muted role has the correct permissions in new channels."""
        try:
            muted_role = get(channel.guild.roles, name="Muted")
            if muted_role:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)
        except Exception as e:
            print(f"Error setting permissions in channel {channel.name}: {e}")


    @cooldown(1, 60, BucketType.user)
    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message is from a bot
        if message.author.bot:
            return
        if self.is_new_member(message.author):
            try:
                support_channel = await self.bot.db.get_support_channel_name(message.guild.id)
                # Check if the message is in the support channel
                if message.channel.name == support_channel:
                    return
                # Check for keywords
                keywords = ["help", "support", "assist", "pack", "how", "how", "how do i", "where", "where do",
                            "where do i", "what", "what do i", "install", "bought", "download", "purchase", "sorry",
                            "solve", "fix", "problem", "issue", "error", "bug", "glitch", "crash", "crashing"]
                if any(keyword in message.content.lower() for keyword in keywords):
                    await message.reply(f"If you are looking for help or support, please go to the #support channel.")
            except commands.CommandOnCooldown:
                # If user is on cooldown, just ignore
                pass
            except Exception as e:
                print(f"Error replying to message in channel {message.channel.name}: {e}")


class RoleSelect(discord.ui.Select):
        def __init__(self, placeholder, roles, action):
            options = [discord.SelectOption(label=role.name, value=str(role.id)) for role in roles]
            super().__init__(placeholder=placeholder, options=options, row=0)
            self.action = action  # either 'add' or 'remove'

        async def callback(self, interaction: discord.Interaction):
            role = interaction.guild.get_role(int(self.values[0]))  # Get the selected role
            user = interaction.user
            
            if self.action == 'add':
                await user.add_roles(role)
                await interaction.response.send_message(f"{user.mention} has been given the {role.name} role.")
            elif self.action == 'remove':
                await user.remove_roles(role)
                await interaction.response.send_message(f"{user.mention} has been removed from the {role.name} role.")


async def setup(bot):
    await bot.add_cog(AdminControls(bot))
