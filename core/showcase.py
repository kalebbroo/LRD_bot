import discord
from discord.ext import commands
from discord.ui import View
from datetime import datetime, timedelta
from discord import ButtonStyle
import random
import asyncio
import aiohttp
import io
import re

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
            await message.edit(embed=embed, attachments=[])

    class ApprovalButtons(View):
        def __init__(self, bot, interaction, original_message, embed):
            super().__init__(timeout=None)
            self.bot = bot
            self.interaction = interaction
            self.original_message = original_message
            self.embed = embed

        @discord.ui.button(style=ButtonStyle.success, label="Approve", custom_id="approve", emoji="✅", row=1)
        async def approve(self, interaction, button):
            guild_id = interaction.guild.id
            showcase_channel_id = await self.bot.get_cog('Database').get_id_from_display(guild_id, "Showcase")

            if showcase_channel_id:
                file = None
                image_url = self.embed.image.url if self.embed.image else None

                if image_url and "attachment://" in image_url:
                    image_data = await self.original_message.attachments[0].read()
                    file = discord.File(io.BytesIO(image_data), filename="image.png")
                    self.embed.set_image(url="attachment://image.png")

                # Remove media URLs from description
                cleaned_description = re.sub(r'https?://\S+', '', self.embed.description)
                self.embed.description = cleaned_description

                # Check if the original embed had the "is_youtube" flag
                is_youtube = any(field.name == 'is_youtube' for field in self.embed.fields)
                view = Showcase.VoteButtons(self.bot, interaction)
                showcase_channel = self.bot.get_channel(showcase_channel_id)

                if is_youtube:
                    showcase_post = await self.youtube_embed_logic(showcase_channel, view)
                else:
                    showcase_post = await showcase_channel.send(embed=self.embed, file=file, view=view)

                thread_name = f"Discussion for {self.original_message.author.name}'s post"
                await showcase_post.create_thread(name=thread_name, auto_archive_duration=1440)  # 1 day

                # Notify the original author via DM
                try:
                    embed_data = {
                        "title": "Showcase Post Approved",
                        "description": f"Your showcase post has been approved by {interaction.user.display_name}.",
                        "color": discord.Color.green(),
                        "footer_text": "Congratulations!"
                    }
                    approval_embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)
                    await self.original_message.author.send(embed=approval_embed)
                except discord.errors.Forbidden:
                    print("Couldn't send DM to user.")

                # Disable buttons
                for button in self.children:
                    button.disabled = True

                # Edit the original message to update the view
                await interaction.message.edit(view=self)

                await interaction.response.send_message(f"Showcase approved by {interaction.user.display_name}!")
                # Give XP to the user who submitted the post
                xp = random.randint(20, 100)
                await self.bot.get_cog('XPCore').add_xp(self.original_message.author.id, self.original_message.guild.id, xp, self.original_message.channel.id)
            else:
                print("Showcase channel not found.")

        async def youtube_embed_logic(self, showcase_channel, view):
            # Get the original embed data
            description = self.embed.description
            title = self.embed.title
            name = self.embed.author.name
            icon_url = self.embed.author.icon_url
            footer = self.embed.footer.text

            # Send the YouTube URL as plain text so Discord does its magic
            youtube_message = await showcase_channel.send(self.original_message.content)
            
            # Wait a bit to ensure Discord has processed the embed. This is a hacky solution.
            await asyncio.sleep(0.3)

            # Fetch the message again to get the auto-generated embed
            fetched_message = await showcase_channel.fetch_message(youtube_message.id)

            # Check if the message has any embeds
            if fetched_message.embeds:
                # Get the first embed (assuming there's only one)
                auto_embed = fetched_message.embeds[0]
                
                # Create a new embed that mimics the auto-generated YouTube embed using your create_embed method
                youtube_embed = await self.bot.get_cog("CreateEmbed").create_embed(
                    title="Click Here to Watch",
                    url=auto_embed.url,
                    description=f"{description}\n\n{auto_embed.description}",
                    image_url=auto_embed.thumbnail.url,
                    color=auto_embed.color,
                    footer_text="Did you like this video? Vote on it below!",
                    author_name=f"{name}",
                    author_icon_url=icon_url,
                )
                # Edit that message to add the new embed and other details
                await youtube_message.edit(content=None, embed=youtube_embed, view=view)
            else:
                print("No embeds found in the message.")
            showcase_post = await youtube_message.edit(content=None, embed=youtube_embed, view=view)
            return showcase_post

        @discord.ui.button(style=ButtonStyle.danger, label="Deny", custom_id="deny", emoji="🖕🏽", row=1)
        async def deny(self, interaction, button):
            try:
                # Notify the user of the denial
                embed_data = {
                    "title": "**Showcase Post Denied**",
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

                # Disable buttons
                for button in self.children:
                    button.disabled = True

                # Edit the original message to update the view
                await interaction.message.edit(view=self)

                await interaction.response.send_message(f"Showcase denied by {interaction.user.display_name}!")
            except discord.errors.Forbidden:
                print("Couldn't send DM to user.")


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        file = None
        showcase_channel_id = await self.db.get_showcase_channel(message.guild.id)
        if not showcase_channel_id or message.channel.id != showcase_channel_id:
            return
        
        # Check if the message contains any links
        any_links = []
        if message.content:
            any_links = re.findall(r'(https?://\S+)', message.content)

        # If the message doesn't have any attachments or URLs, delete it
        if not message.attachments and not any_links:
            await message.delete()
            embed_data = {
                "title": "**Invalid Showcase Post**",
                "description": """Your showcase post must include media to be showcased with a description. Please try again. \
                If you believe this is an error, please contact an admin. \
                All submissions should contain LRD content and are subject to approval.""",
                "color": discord.Color.red()
            }
            embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)
            await message.author.send(embed=embed)
            return

        # Create the initial embed data
        embed_data = {
            "title": f"Join the LittleRoomDev Patreon!",
            "url": "https://www.patreon.com/littleroomdev",
            "description": message.content,
            "color": discord.Color.blue(),
            "author_name": f"Submitted Showcase by {message.author.display_name}",
            "author_icon_url": message.author.avatar.url,
            "footer_text": f"Vote Below!"
        }
        is_youtube = False 
        # Check for valid media links
        valid_media_links = [link for link in any_links if any(extension in link for extension in ['.jpg', '.jpeg', '.png', '.gif', '.mp4'])]

        if valid_media_links:
            # Download the image and create a File object
            async with aiohttp.ClientSession() as session:
                async with session.get(valid_media_links[0]) as resp:
                    if resp.status == 200:
                        data = io.BytesIO(await resp.read())
                        file = discord.File(data, filename="image.png")
            embed_data["image_url"] = "attachment://image.png"

        elif 'youtube.com' in message.content or 'youtu.be' in message.content:
            # Handle YouTube links
            embed_data["fields"] = [("YouTube Video", "Pending Approval", False)]
            is_youtube = True  # Set the flag as True for YouTube links

        # Attach uploaded media if available
        if message.attachments:
            image_data = await message.attachments[0].read()
            file = discord.File(io.BytesIO(image_data), filename="image.png")
            embed_data["image_url"] = "attachment://image.png"

        if is_youtube:  # Add this condition to add the flag into the embed data
            embed_data["fields"].append(("is_youtube", "True", False))

        admin_channel_id = await self.db.get_admin_channel(message.guild.id)
        if admin_channel_id:
            admin_channel = self.bot.get_channel(admin_channel_id)

            # Convert the embed_data to an actual embed
            embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)

            # If there's a valid media link, set it as the image in the embed
            if valid_media_links:
                embed.set_image(url=valid_media_links[0])

            # If there's an uploaded image, set it as the image in the embed
            if message.attachments:
                embed.set_image(url="attachment://showcase.jpg")

            # Send the embed to the admin channel for approval
            view = self.ApprovalButtons(self.bot, None, message, embed)
            await admin_channel.send(embed=embed, file=file if file else None, view=view)

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
            await message.channel.send("Error finding admin channel. Report this error to an Admin")


async def setup(bot):
    await bot.add_cog(Showcase(bot))