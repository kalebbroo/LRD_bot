import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import time
import json

class WarnCore(commands.Cog):
    """
    Cog responsible for handling user warnings in the server.
    """
    def __init__(self, bot: commands.Bot):
        """Initialize the WarnCore with the bot object."""
        self.bot = bot
        self.db_cog = self.bot.get_cog('Database')
        self.embed_cog = self.bot.get_cog('CreateEmbed')

    @app_commands.command(name='warn', description='Log a warning for a user')
    @app_commands.describe(member='The member to warn')
    @app_commands.describe(reason='The reason for the warn')
    @app_commands.checks.has_permissions(administrator=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        """
        Warn a user and log the warning to the database.
        """
        try:
            await interaction.response.defer()
            user_id = member.id
            guild_id = interaction.guild.id

            # Retrieve user data from the database
            user = await self.db_cog.handle_user(guild_id, "get", user_id=user_id)
            warnings = json.loads(user['warnings'])

            # Append new warning details to the list
            warnings.append({
                "guild_id": guild_id,
                "user_id": user_id,
                "issuer_id": interaction.user.id,
                "time": time.time(),
                "reason": reason
            })

            user['warnings'] = json.dumps(warnings)
            
            # Update user data in the database
            await self.db_cog.handle_user(guild_id, "update", user_id=user_id, user_data=user)

            # Create embed using CreateEmbed cog
            fields = [
                ("📊 User Stats", f"Level: {user['level']}\nXP: {user['xp']}\nTotal Warnings: {len(warnings)}", False),
                (f"⚠️ Warned by {interaction.user.display_name}", f"**Reason:** {reason}", False),
                ("🔔 Notice", "Repeated warnings may result in being muted or kicked from the server. Please follow the rules.", False)
            ]
            embed = await self.embed_cog.create_embed(
                title="⚠️ Warning Issued ⚠️",
                color=0xff0000,
                author_name=member.display_name,
                author_icon_url=member.display_avatar.url,
                fields=fields
            )
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            # Send an error message in case of any unexpected error
            await interaction.followup.send(f"An error occurred: {str(e)}")

    @app_commands.command(name='view_warnings', description='View all warnings of a user')
    @app_commands.describe(member='The member to view warnings of')
    async def view_warnings(self, interaction: discord.Interaction, member: discord.Member):
        """
        View all warnings of a specified user.
        """
        try:
            await interaction.response.defer()
            user_id = member.id
            guild_id = interaction.guild.id

            # Retrieve user data from the database
            user = await self.db_cog.handle_user(guild_id, "get", user_id=user_id)
            warnings = json.loads(user['warnings'])

            if len(warnings) == 0:
                await interaction.followup.send(f"{member.display_name} has no warnings.")
                return

            color = 0x00ff00 if len(warnings) == 1 else 0xff0000
            fields = [("📊 User Stats", f"Level: {user['level']}\nXP: {user['xp']}\nTotal Warnings: {len(warnings)}", False)]

            for warning in warnings:
                issuer = await interaction.guild.fetch_member(warning["issuer_id"])
                timestamp = datetime.fromtimestamp(warning["time"]).strftime('%Y-%m-%d %H:%M:%S')
                fields.append((f"⚠️ Warned on {timestamp} by {issuer.display_name}", f"**Reason:** {warning['reason']}", False))

            # Create embed using CreateEmbed cog
            embed = await self.embed_cog.create_embed(
                title="⚠️ Warnings ⚠️",
                color=color,
                author_name=member.display_name,
                author_icon_url=member.display_avatar.url,
                fields=fields
            )
            await interaction.followup.send(embed=embed)

        except Exception as e:
            # Send an error message in case of any unexpected error
            await interaction.followup.send(f"An error occurred: {str(e)}")

async def setup(bot):
    """Load the WarnCore cog."""
    await bot.add_cog(WarnCore(bot))
