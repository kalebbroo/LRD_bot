from discord.ext.commands import BucketType, cooldown
from discord import app_commands, Embed, Colour
from datetime import datetime, timedelta
from typing import List, Union
from discord.ext import commands
from discord.utils import get
import discord

class AdminControls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.get_cog("Database")
        self.embed_cog = self.bot.get_cog("CreateEmbed")

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
            embed_data = {
                "title": "Mute",
                "description": f"{user.mention} has been muted.",
                "color": Colour.red(),
                "fields": [{"name": "Reason", "value": reason}] if reason else []
            }
            embed = await self.embed_cog.create_embed(interaction, **embed_data)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed_data = {
                "title": "Error",
                "description": f"An error occurred: {e}",
                "color": Colour.red()
            }
            embed = await self.embed_cog.create_embed(interaction, **embed_data)
            await interaction.followup.send(embed=embed, ephemeral=True)


    @app_commands.command(name='unmute', description='Unmute a member')
    @app_commands.describe(user='The member to mute')
    async def unmute(self, interaction, user: discord.Member):
        await interaction.response.defer()
        try:
            role = get(interaction.guild.roles, name="Muted")
            if role in user.roles:
                await user.remove_roles(role)
                embed_data = {
                "title": "Unmute",
                "description": f"{user.mention} has been unmuted.",
                "color": Colour.green()
            }
            embed = await self.embed_cog.create_embed(interaction, **embed_data)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed_data = {
                "title": "Error",
                "description": f"An error occurred: {e}",
                "color": Colour.red()
            }
            embed = await self.embed_cog.create_embed(interaction, **embed_data)
            await interaction.followup.send(embed=embed, ephemeral=True)

    # TODO: fix mod log db entry
    @app_commands.command(name='kick', description='Kick a member from the server')
    @app_commands.describe(user='The member to kick', reason='The reason for the kick')
    async def kick(self, interaction, user: discord.Member, reason: str):
        """Kick a member from the server."""
        await interaction.response.defer()
        try:
            await user.kick(reason=reason)
            
            embed_data = {
                "title": "Kick",
                "description": f"{user.mention} has been kicked for {reason}.",
                "color": Colour.orange()
            }
            embed = await self.embed_cog.create_embed(interaction, **embed_data)
            await interaction.followup.send(embed=embed)
            
            #await self.db.add_moderation_log(interaction.guild.id, "kick", user.id, interaction.user.id, reason, datetime.utcnow().timestamp())
        except Exception as e:
            embed_data = {
                "title": "Error",
                "description": f"An error occurred: {e}",
                "color": Colour.red()
            }
            embed = await self.embed_cog.create_embed(interaction, **embed_data)
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f"An error occurred: {e}")


    @app_commands.command(name='ban', description='Ban a member from the server')
    @app_commands.describe(user='The member to ban', reason='The reason for the ban')
    async def ban(self, interaction, user: discord.Member, reason: str):
        """Ban a member from the server."""
        await interaction.response.defer()
        try:
            await user.ban(reason=reason)
            
            embed_data = {
                "title": "Ban",
                "description": f"{user.mention} has been banned for {reason}.",
                "color": Colour.dark_red()
            }
            embed = await self.embed_cog.create_embed(interaction, **embed_data)
            await interaction.followup.send(embed=embed)
            
            await self.db.add_moderation_log(interaction.guild.id, "ban", user.id, interaction.user.id, reason, datetime.utcnow().timestamp())
        except Exception as e:
            embed_data = {
                "title": "Error",
                "description": f"An error occurred: {e}",
                "color": Colour.red()
            }
            embed = await self.embed_cog.create_embed(interaction, **embed_data)
            await interaction.followup.send(embed=embed, ephemeral=True)
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
                embed_data = {
                    "title": "Error",
                    "description": "Invalid action. Please enter 'add' or 'remove'.",
                    "color": discord.Colour.red()
                }
                embed = await self.embed_cog.create_embed(interaction, **embed_data)
                await interaction.followup.send(embed=embed)
                return
            embed_data = {
                "title": "Role Adjustment",
                "description": f"Please select a role to {action} for {user.mention}:",
                "color": discord.Colour.blue()
            }
            embed = await self.embed_cog.create_embed(interaction, **embed_data)
            view = discord.ui.View()
            view.add_item(select)
            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            embed_data = {
                "title": "Error",
                "description": f"An error occurred: {e}",
                "color": discord.Colour.red()
            }
            embed = await self.embed_cog.create_embed(interaction, **embed_data)
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f"An error occurred: {e}")

    # TODO: have the channels and roles populated from the database
    @app_commands.command(name='announcement', description='Post an announcement in a specified channel')
    @app_commands.describe(
        title="Title of the Announcement",
        message="Content of the Announcement",
        channel="The channel where the announcement should be posted",
        tag_a_role="Roles to tag in the announcement (optional)",
        media_url="URL of the media to be displayed (optional)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def announcement(self, interaction, title: str, message: str, channel: discord.TextChannel, 
                        tag_a_role: discord.Role = None, media_url: str = None):
        await interaction.response.defer(ephemeral=True)

        # Check if the user attached any media
        if interaction.message and interaction.message.attachments:
            media_url = interaction.message.attachments[0].url
        footer = "test"
        embed_data = {
            "title": title,
            "description": message,
            "color": discord.Color.blue(),
            "footer_text": footer,
        }
        embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)

        if media_url:
            embed.set_image(url=media_url)
        mention_role = ""
        if tag_a_role:
            mention_role = f"<@&{tag_a_role.id}>"

        # Send the embed to the specified channel
        await interaction.followup.send("Announcement successfully posted.", ephemeral=True)
        await channel.send(content=mention_role, embed=embed)


    @commands.Cog.listener()
    async def on_channel_create(self, channel):
        """Ensure the Muted role has the correct permissions in new channels."""
        try:
            muted_role = get(channel.guild.roles, name="Muted")
            if muted_role:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)
        except Exception as e:
            print(f"Error setting permissions in channel {channel.name}: {e}")

    # TODO: Fix this to only send the message to users below level 2
    @cooldown(1, 60, BucketType.user)
    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message is from a bot
        if message.author.bot:
            return
        db_cog = self.bot.get_cog('Database')
        not_silent = discord.utils.get(message.author.roles, name="Not Silent")
        print(f"not_silent: {not_silent}")
        if not not_silent:
            try:
                # Check for keywords
                keywords = ["help", "support", "assist", "pack", "how", "fix", "where", "why",
                            "what", "install", "bought", "download", "purchase", "sorry",
                            "solve", "fix", "problem", "issue", "error", "bug", "glitch", "crash", "crashing",
                            "mcmodels", "buy", "patreon", "npc", "citizens", "mythicmobs", "modelengine", "meg", "meg4",]
                if any(keyword in message.content.lower() for keyword in keywords):
                    embed_data = {
                        "title": "Need Help?",
                        "description": (
                                        "If you are looking for help or support, "
                                        "please go to the #support channel and make a ticket. "
                                        "No support will be given in general channels.\n\n"
                                        "Need support on a pack purchased from MCModels? "
                                        "You have to make a support ticket on their Discord. "
                                        "We are not able to provide support here for MCModels packs.\n\n"
                                        "Need help installing a pack? Check out #how-to-install and #faq.\n\n"
                                        "Support for Patreon content is a PERK of being a Patron. "
                                        "Link your Discord account to your Patreon account and you will be "
                                        "automatically given a role for support tickets and teh #patreon channel."
                                    ),
                        "color": discord.Colour.red()
                    }
                    embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)
                    await message.reply(embed=embed)
            except commands.CommandOnCooldown:
                # If user is on cooldown, just ignore
                pass
            except Exception as e:
                print(f"Error replying to message in channel {message.channel.name}: {e}")



class RoleSelect(discord.ui.Select):
    def __init__(self, bot, placeholder, roles, action):
        options = [discord.SelectOption(label=role.name, value=str(role.id)) for role in roles]
        super().__init__(placeholder=placeholder, options=options, row=0)
        self.bot = bot
        self.action = action  # either 'add' or 'remove'

    async def callback(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(int(self.values[0]))  # Get the selected role
        user = interaction.user
        embed_data = {
            "color": discord.Colour.blue(),
        }
        if self.action == 'add':
            await user.add_roles(role)
            embed_data["description"] = f"{user.mention} has been given the {role.name} role."
        elif self.action == 'remove':
            await user.remove_roles(role)
            embed_data["description"] = f"{user.mention} has been removed from the {role.name} role."
        embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(AdminControls(bot))
