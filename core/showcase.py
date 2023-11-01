import discord
from discord.ext import commands
from discord.ui import View
from discord import ButtonStyle, Message, File, Color
from aiohttp import ClientSession
import random
import asyncio
import urllib
import io
import re
import os

class Showcase(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.get_cog("Database")

    class VoteButtons(View):
        def __init__(self, bot, interaction):
            super().__init__(timeout=None)
            self.bot = bot
            self.interaction = interaction
        @discord.ui.button(style=ButtonStyle.success, label="Vote Up", custom_id="vote_up", emoji="👍", row=1)
        async def vote_up(self, interaction, button):
            user = interaction.user.id
            message_id = interaction.message.id
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
                temp_file_path = None
                is_image = False  # New variable to check if the attachment is an image
                
                if self.original_message.attachments:
                    attachment = self.original_message.attachments[0]
                    file_extension = os.path.splitext(attachment.filename)[1]
                    if any(attachment.filename.endswith(ext) for ext in ['.mp4', '.mkv', '.flv', '.webm', '.jpg', '.png', '.gif']):
                        temp_file_path = f"./temp/{self.original_message.id}{file_extension}"
                        file = discord.File(temp_file_path, filename=f"media{file_extension}")
                        is_image = attachment.filename.endswith(('.jpg', '.png', '.gif', '.jpeg', '.webp'))

                # Remove media URLs from description
                cleaned_description = re.sub(r'https?://\S+', '', self.embed.description)
                self.embed.description = cleaned_description

                # Check if the original embed had the "is_youtube" flag
                is_youtube = any(field.name == 'is_youtube' for field in self.embed.fields)
                view = Showcase.VoteButtons(self.bot, interaction)
                showcase_channel = self.bot.get_channel(showcase_channel_id)

                # If this is not a YouTube post
                if not is_youtube:
                    if file:
                        if is_image:
                            self.embed.set_image(url=f"attachment://media{file_extension}")  # If it's an image, set it in the embed
                        showcase_post = await showcase_channel.send(embed=self.embed, file=file, view=view)
                    else:
                        showcase_post = await showcase_channel.send(embed=self.embed, view=view)

                if temp_file_path:  # Delete the temporary file if it exists
                    os.remove(temp_file_path)

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
    async def on_message(self, message: Message) -> None:
        if message.author.bot:
            return
        # Initialize variables
        file = None
        temp_file_path = None
        showcase_channel_id = await self.db.get_showcase_channel(message.guild.id)
        is_youtube = False
        embed_data = {
            "title": f"Join the LittleRoomDev Patreon!",
            "url": "https://www.patreon.com/littleroomdev",
            "description": message.content,
            "color": Color.blue(),
            "author_name": f"Submitted Showcase by {message.author.display_name}",
            "author_icon_url": message.author.avatar.url,
            "footer_text": f"Vote Below!"
        }
        # Check if the message is in the showcase channel
        if not showcase_channel_id or message.channel.id != showcase_channel_id:
            return
        
        # Check for any links in the message content
        any_links = re.findall(r'(https?://\S+)', message.content) if message.content else []
        
        # Reject and delete messages that don't contain any media or URLs
        if not message.attachments and not any_links:
            await self.reject_invalid_post(message)
            return

        # Check for valid media URLs
        valid_media_links = [link for link in any_links if any(ext in link for ext in ['.jpg', '.jpeg', '.png', '.gif', '.mp4'])]
        if valid_media_links:
            first_valid_link = valid_media_links[0]
            parsed_url = urllib.parse.urlparse(first_valid_link)
            file_extension = os.path.splitext(parsed_url.path)[1]
            async with ClientSession() as session:
                async with session.get(first_valid_link) as resp:
                    if resp.status == 200:
                        data = io.BytesIO(await resp.read())
                        file = File(data, filename=f"media{file_extension}")
            embed_data["image_url"] = f"attachment://media{file_extension}"

        # Check for YouTube links
        elif 'youtube.com' in message.content or 'youtu.be' in message.content:
            embed_data["fields"] = [("YouTube Video", "Pending Approval", False)]
            is_youtube = True

        # Handle uploaded media (if available)
        if message.attachments:
            attachment = message.attachments[0]
            file_extension = os.path.splitext(attachment.filename)[1]
            
            # For video files
            if any(attachment.filename.endswith(ext) for ext in ['.mp4', '.mkv', '.flv', '.webm']):
                temp_file_path = await self.handle_video_attachment(await attachment.read(), file_extension, message.id)
                file = File(temp_file_path, filename=f"file{file_extension}")

            # For image files (Newly Added)
            else:
                async with ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status == 200:
                            # Create a temporary folder if it doesn't exist
                            if not os.path.exists('./temp'):
                                os.makedirs('./temp')
                            
                            # Define the path for the temporary file
                            temp_file_path = f"./temp/{message.id}{file_extension}"
                            
                            # Save the file to the temporary location
                            with open(temp_file_path, 'wb') as f:
                                f.write(await resp.read())

                # Create a discord.File object with the temporary file
                file = File(temp_file_path, filename=f"media{file_extension}")

                # Update the embed to use the file
                embed_data["image_url"] = f"attachment://media{file_extension}"

        if is_youtube:
            embed_data["fields"].append(("is_youtube", "True", False))

        await self.handle_admin_channel_post(embed_data, valid_media_links, file, message)

    async def reject_invalid_post(self, message: Message) -> None:
        embed_data = {
            "title": "**Invalid Showcase Post**",
            "description": """Your showcase post must include media to be showcased with a description. Please try again. \
            If you believe this is an error, please contact an admin. \
            All submissions should contain LRD content and are subject to approval.""",
            "color": discord.Color.red()
        }
        embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)
        await message.author.send(embed=embed)
        await message.delete()

    async def handle_video_attachment(self, attachment_data: bytes, file_extension: str, message_id: int) -> str:
        if not os.path.exists('./temp'):
            os.makedirs('./temp')
        temp_file_path = f"./temp/{message_id}{file_extension}"
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(attachment_data)
        return temp_file_path

    async def handle_admin_channel_post(self, embed_data: dict, valid_media_links: list, file: discord.File, message: Message) -> None:
        admin_channel_id = await self.db.get_admin_channel(message.guild.id)
        if admin_channel_id:
            admin_channel = self.bot.get_channel(admin_channel_id)
            embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)

            if valid_media_links:
                embed.set_image(url=valid_media_links[0])

            view = self.ApprovalButtons(self.bot, None, message, embed)
            await admin_channel.send(embed=embed, file=file if file else None, view=view)

            await message.delete()

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