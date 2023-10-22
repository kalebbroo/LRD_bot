import discord
from discord.ext import commands
from discord.ui import View
from datetime import datetime, timedelta
from discord import ButtonStyle
import random
import asyncio
import io

class Showcase(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.get_cog("Database")

    class VoteButtons(View):
        def __init__(self, bot, interaction):
            super().__init__(timeout=None)
            self.bot = bot
            self.interaction = interaction
        # TODO: make sure all methods in the db cog work with code changes
        @discord.ui.button(style=ButtonStyle.success, label="Vote Up", custom_id="vote_up", emoji="👍", row=1)
        async def vote_up(self, interaction, button):
            user = interaction.user.id
            message_id = interaction.message.id
            db = self.bot.get_cog("Database")
            guild_id = interaction.guild.id
            vote_added = await db.add_vote(guild_id, message_id, user, 'vote_up')
            if not vote_added:
                await interaction.response.send_message(f"You've already voted on this post!", ephemeral=True)
                return
            await self.update_embed_with_votes(guild_id, interaction.message, message_id)
            await interaction.response.send_message(f"Thanks for your vote!", ephemeral=True)
            xp = 10  # You can adjust the XP value as needed
            await self.bot.get_cog('XPCore').add_xp(interaction.user.id, interaction.guild.id, xp, interaction.channel.id)
        
        @discord.ui.button(style=ButtonStyle.success, label="Vote Down", custom_id="vote_down", emoji="👎", row=1)
        async def vote_down(self, interaction, button):
            user = interaction.user.id
            message_id = interaction.message.id
            db = self.bot.get_cog("Database")
            guild_id = interaction.guild.id
            vote_added = await db.add_vote(guild_id, message_id, user, 'vote_down')
            if not vote_added:
                await interaction.response.send_message(f"You've already voted on this post!", ephemeral=True)
                return
            await self.update_embed_with_votes(guild_id, interaction.message, message_id)
            await interaction.response.send_message(f"Thanks for your vote!", ephemeral=True)

        async def update_embed_with_votes(self, guild_id, message, message_id):
            db = self.bot.get_cog("Database")
            upvotes = await db.get_vote_count_for_post(guild_id, message_id, "vote_up")
            downvotes = await db.get_vote_count_for_post(guild_id, message_id, "vote_down")
            is_leader = await db.is_leading_post(guild_id, message_id)
            
            # Get the current embed from the message
            embed = message.embeds[0]
            
            # Update the footer with the new vote count
            leader_text = "🏆 Current Leader!" if is_leader else ""
            embed.set_footer(text=f"# of Upvotes: {upvotes} |⚖️| # of Downvotes: {downvotes} {leader_text}")
            
            # Edit the message with the updated embed
            await message.edit(embed=embed)

    class ApprovalButtons(View):
        def __init__(self, bot, interaction, original_message, embed):
            super().__init__(timeout=None)
            self.bot = bot
            self.interaction = interaction
            self.original_message = original_message
            self.embed = embed

        @discord.ui.button(style=ButtonStyle.success, label="Approve", custom_id="approve", emoji="✅", row=1)
        async def approve(self, interaction, button):
            guild_id = interaction.guild.id  # Get the guild ID from the interaction
            showcase_channel_id = await self.bot.get_cog('Database').get_id_from_display(guild_id, "Showcase")
            
            if showcase_channel_id:
                # Send the embed (with the image URL) to the showcase channel
                view = Showcase.VoteButtons(self.bot, interaction)
                
                # Get the actual channel object using the ID
                showcase_channel = self.bot.get_channel(showcase_channel_id)
                showcase_post = await showcase_channel.send(embed=self.embed, view=view)

                # Open a thread on the embed that was posted in the showcase
                thread_name = f"Discussion for {self.original_message.author.name}'s post"
                await showcase_post.create_thread(name=thread_name, auto_archive_duration=1440)  # 1 day
                await interaction.response.send_message("Showcase approved!")

                # Award the user with random XP
                xp = random.randint(20, 100)
                await self.bot.get_cog('XPCore').add_xp(self.original_message.author.id, self.original_message.guild.id, xp, self.original_message.channel.id)
            else:
                print("Showcase channel not found.")

        @discord.ui.button(style=ButtonStyle.danger, label="Deny", custom_id="deny", emoji="🖕🏽", row=1)
        async def deny(self, interaction, button):
            try:
                # Notify the user of the denial
                embed_data = {
                    "title": "Showcase Post Denied",
                    "description": "Your showcase post was denied by the admins. Please ensure it meets the following guidelines:",
                    "color": discord.Color.red(),
                    "fields": [
                        ("LittleRoomDev Content", "The main purpose of this showcase channel is to showcase LittleRoomDev content you are using on your server.", False),
                        ("NSFW Content", "Ensure there's no NSFW or inappropriate content in your post.", False),
                        ("Relevance", "Make sure your post is relevant to the theme of the showcase channel.", False),
                        ("No Spam", "Avoid spamming or posting duplicate content.", False)
                    ],
                    "footer_text": "Thank you for understanding!"
                }
                embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)
                await self.original_message.author.send(embed=embed)
                await interaction.response.send_message("Showcase denied!")
            except discord.errors.Forbidden:
                print("Couldn't send DM to user.")


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        showcase_channel_id = await self.db.get_showcase_channel(message.guild.id)
        if not showcase_channel_id or message.channel.id != showcase_channel_id:
            return

        if not message.attachments or not message.content:
            await message.delete()
            embed_data = {
                "title": "Invalid Showcase Post",
                "description": "Your showcase post must include media and a description. Please try again.",
                "color": discord.Color.red()
            }
            embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)
            await message.author.send(embed=embed)
            return

        last_post_time = await self.db.get_last_post_time(message.author.id, message.guild.id)
        if last_post_time and datetime.utcnow() - last_post_time < timedelta(days=1):
            await message.delete()
            await message.author.send("You can only post once every 24 hours in the showcase channel.")
            return

        # Create the initial embed data
        embed_data = {
            "title": f"Showcase LRD Content by {message.author.display_name}",
            "description": message.content,
            "color": discord.Color.blue(),
            "author_name": message.author.display_name,
            "author_icon_url": message.author.avatar.url,
            "footer_text": f"Posted by {message.author.name}"
        }
        admin_channel_id = await self.db.get_admin_channel(message.guild.id)
        if admin_channel_id:
            admin_channel = self.bot.get_channel(admin_channel_id)

            # Send the image to the admin channel
            image_data = await message.attachments[0].read()
            file = discord.File(io.BytesIO(image_data), filename="showcase.jpg")
            image_message = await admin_channel.send(file=file)

            # Use the uploaded image URL for the embed
            embed_data["image_url"] = image_message.attachments[0].url

            # Convert the embed_data to an actual embed
            embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)

            # Send the embed to the admin channel for approval
            view = self.ApprovalButtons(self.bot, None, message, embed)
            await admin_channel.send(embed=embed, view=view)

            # Delete the original message
            await message.delete()

            # Notify the user of submission
            embed_data = {
                "title": "Showcase Post Submitted",
                "description": "Your showcase post has been submitted to the admin for approval.",
                "color": discord.Color.blue()
            }
            embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)
            await message.author.send(embed=embed)
        else:
            await message.channel.send("Error finding admin channel. Report this error to an Admin.")


async def setup(bot):
    await bot.add_cog(Showcase(bot))