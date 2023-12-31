import discord
from discord.ext import commands
from discord.ui import View
from discord import ButtonStyle, Message, File, Color
from aiohttp import ClientSession
from imgurpython import ImgurClient
import random
import asyncio
import aiohttp
import urllib
import io
import re
import os

cooldown = False

class Showcase(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.get_cog("Database")

    class VoteButtons(View):
        def __init__(self, bot):
            super().__init__(timeout=None)
            self.bot = bot
            self.db = bot.get_cog("Database")

        async def handle_vote(self, interaction: discord.Interaction, vote_type: str):
            user_id = interaction.user.id
            message_id = interaction.message.id
            guild_id = interaction.guild.id
            global cooldown

            # Check if the user is on cooldown
            if cooldown:
                await interaction.response.send_message("**DO NOT SPAM THE BUTTONS!** Please wait 5 seconds before trying again.", ephemeral=True)
                return

            # Retrieve the current vote status for the user and message
            current_vote = await self.db.handle_showcase(guild_id, "get_vote_status", user_id=user_id, message_id=message_id)

            # Determine if the user has voted before and their previous vote type
            has_voted = current_vote is not None and (int(current_vote[0]) == 1 or int(current_vote[1]) == 1)
            has_voted_same_before = False
            has_voted_opposite_before = False

            if has_voted:
                vote_up, vote_down = current_vote
                vote_up = int(vote_up)
                vote_down = int(vote_down)
                has_voted_same_before = (vote_type == "vote_up" and vote_up == 1) or (vote_type == "vote_down" and vote_down == 1)
                has_voted_opposite_before = (vote_type == "vote_up" and vote_down == 1) or (vote_type == "vote_down" and vote_up == 1)

            # Construct the response message based on the vote status
            if has_voted_same_before:
                response_message = "You have already voted on this post!"
            elif has_voted_opposite_before:
                response_message = "You have changed your vote."
                await self.db.handle_showcase(guild_id, "change_vote", user_id=user_id, message_id=message_id, vote_type=vote_type)
            elif not has_voted:
                success = await self.db.handle_showcase(guild_id, "add_vote", user_id=user_id, message_id=message_id, vote_type=vote_type)
                if success:
                    response_message = "Thanks for your vote!"
                    await self.bot.get_cog('XPCore').add_xp(user_id, guild_id, 10, interaction.channel.id)
                else:
                    response_message = "There was an error recording your vote. Please try again."
            else:
                response_message = "There was an error with your vote. Please try again."

            # Get the current embed from the message
            current_embed = interaction.message.embeds[0]

            # Update the embed with the new vote counts
            upvotes = await self.db.handle_showcase(guild_id, "get_vote_count", message_id=message_id, vote_type="vote_up")
            downvotes = await self.db.handle_showcase(guild_id, "get_vote_count", message_id=message_id, vote_type="vote_down")
            is_leader = await self.db.handle_showcase(guild_id, "is_leading_post", message_id=message_id)
            leader_text = "🏆 Current Leader!" if is_leader else ""
            new_embed = discord.Embed.from_dict(current_embed.to_dict())
            new_embed.set_footer(text=f"👍 {upvotes} |⚖️| 👎 {downvotes} {leader_text}")

            # Edit the message with the updated embed and re-upload the file if it exists
            await interaction.message.edit(embed=new_embed)

            # Respond to the user's interaction
            await interaction.response.send_message(response_message, ephemeral=True)
            cooldown = True
            await asyncio.sleep(5)
            cooldown = False

        @discord.ui.button(style=ButtonStyle.success, label="Vote Up", custom_id="vote_up", emoji="👍", row=1)
        async def vote_up(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.handle_vote(interaction, "vote_up")

        @discord.ui.button(style=ButtonStyle.success, label="Vote Down", custom_id="vote_down", emoji="👎", row=1)
        async def vote_down(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.handle_vote(interaction, "vote_down")

    class ApprovalButtons(View):
        def __init__(self, bot, original_message, embed):
            super().__init__(timeout=None)
            self.bot = bot
            self.original_message = original_message
            self.embed = embed
            self.db = bot.get_cog("Database")

        @discord.ui.button(style=ButtonStyle.success, label="Approve", custom_id="approve", emoji="✅", row=1)
        async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
            guild_id = interaction.guild.id
            video_url = re.findall(r'(https?://\S+)', self.embed.description) if self.embed.description else []
            showcase_channel_id = await self.db.handle_channel(guild_id, "get_showcase_channel", display_name="Showcase")

            if not showcase_channel_id:
                print("Showcase channel ID not found.")
                return
            showcase_channel = self.bot.get_channel(showcase_channel_id)

            await showcase_channel.send(f"{video_url}") if video_url else None
            showcase_post = await showcase_channel.send(embed=self.embed, view=Showcase.VoteButtons(self.bot))

            # Add the message id to the database
            await self.db.handle_showcase(guild_id, "save_new_showcase", user_id=self.original_message.author.id, message_id=showcase_post.id)
            print(f"Showcase post saved to database with message ID {showcase_post.id}")

            # Create a thread for discussion
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
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True

            # Edit the original message to update the view
            await interaction.message.edit(view=self)

            await interaction.response.send_message(f"Showcase approved by {interaction.user.display_name}!")

            # Give XP to the user who submitted the post
            xp = random.randint(20, 100)
            await self.bot.get_cog('XPCore').add_xp(self.original_message.author.id, self.original_message.guild.id, xp, self.original_message.channel.id)

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

    async def video_embed_logic(self, message, channel, view):
            # Wait a bit to ensure Discord has processed the embed. This is a hacky solution.
            await asyncio.sleep(0.2)
            # Fetch the message again to get the auto-generated embed
            fetched_message = await channel.fetch_message(message.id)

            # Check if the message has any embeds
            if fetched_message.embeds:
                # Get the first embed (assuming there's only one)
                vid_embed = fetched_message.embeds[0]
                # Get the original embed data
                description = vid_embed.description
                title = vid_embed.title
                name = vid_embed.author.name
                icon_url = vid_embed.author.icon_url
                footer = vid_embed.footer.text
                
                # Create a new embed that mimics the auto-generated YouTube embed using your create_embed method
                video_embed = await self.bot.get_cog("CreateEmbed").create_embed(
                    title="Click Here to Watch",
                    url=vid_embed.url,
                    description=f"{description}\n\n{vid_embed.description}",
                    image_url=vid_embed.thumbnail.url,
                    color=vid_embed.color,
                    footer_text="Did you like this video? Vote on it below!",
                    author_name=f"{name}",
                    author_icon_url=icon_url,
                )
                # Edit that message to add the new embed and other details
                await message.edit(content=None, embed=video_embed, view=view)
            else:
                print("No embeds found in the message.")
            showcase_post = await message.edit(content=None, embed=video_embed, view=view)
            return showcase_post
    
    async def upload_to_imgur(self, image_path):
        client_id = os.getenv('IMGUR_CLIENT_ID')
        client_secret = os.getenv('IMGUR_CLIENT_SECRET')

        client = ImgurClient(client_id, client_secret)

        # Upload an image
        upload_result = client.upload_from_path(image_path, anon=True)

        # Get the image URL
        image_url = upload_result['link']
        print("Uploaded image URL:", image_url)
        return image_url


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        # Fetch showcase channel ID from the database
        showcase_channel_id = await self.db.handle_channel(message.guild.id, "get_showcase_channel")
        try:
            # Initialize variables
            is_youtube = False
            embed_data = {
                "title": f"Join the LittleRoomDev Patreon!",
                "url": "https://www.patreon.com/littleroomdev",
                "description": message.content,
                "color": discord.Color.blue(),
                "author_name": f"Submitted Showcase by {message.author.display_name}",
                "author_icon_url": message.author.avatar.url,
                "footer_text": f"Vote Below if you like their showcase!"
            }
            # Check if the message is in the showcase channel
            if message.channel.id != showcase_channel_id:
                print("Message not in showcase channel. Skipping.")
                return

            # Check for any links in the message content
            any_links = re.findall(r'(https?://\S+)', message.content) if message.content else []

            # Reject and delete messages that don't contain any media or URLs
            if not message.attachments and not any_links or not message.content or len(message.content) > 2000:
                await self.reject_invalid_post(message)
                return

            # Check for YouTube links and set is_youtube flag
            if 'youtube.com' in message.content or 'youtu.be' in message.content:
                is_youtube = True
                embed_data["fields"] = [("YouTube Video", "Pending Approval", False), ("is_youtube", "True", False)]
            is_streamable = False
            if 'streamable.com' in message.content:
                is_streamable = True

            # Filter out valid media links
            # Valid image formats
            valid_image_links = [link for link in any_links if any(ext in link for ext in ['.jpg', '.jpeg', '.png', '.gif', '.tiff', '.apng'])]

            # Send a placeholder message to the admin channel and obtain its ID
            admin_channel_id = await self.db.handle_channel(message.guild.id, "get_admin_channel")
            if not admin_channel_id:
                print("Admin channel ID not found.")
                return
            admin_channel = self.bot.get_channel(admin_channel_id)

            # Valid video file extensions
            video_ext = ['.mp4', '.mpeg', '.avi', '.webm', '.mov', '.mkv', '.flv', '.wmv', '.asf']
            # Check message attachments for video files
            valid_video = [attachment for attachment in message.attachments if any(attachment.filename.lower().endswith(ext) for ext in video_ext)]
            # Combine image and video attachments
            valid_media_attachments = valid_video + [attachment for attachment in message.attachments 
                                                     if any(attachment.filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.tiff', '.apng'])]
            if is_youtube or is_streamable:
                print(f"\nStreaming Video link found.\n")
                placeholder_message = await admin_channel.send(f"{message.content}")
                await asyncio.sleep(0.1)
                fetched_message = await admin_channel.fetch_message(placeholder_message.id)
                # Instantiate your ApprovalButtons view
                view = self.ApprovalButtons(self.bot, message, fetched_message.embeds[0])
                await self.video_embed_logic(placeholder_message, admin_channel, view)

            # Determine the media URL and download media if not a YouTube link
            else:
                valid_media = valid_media_attachments if valid_media_attachments else valid_image_links
                if valid_media:
                    if valid_video:
                        video_message = await admin_channel.send(f"{message.content}")
                    placeholder_message = await admin_channel.send(f"{message.content}") 
                    media_url = valid_media[0].url if message.attachments else valid_media[0]
                    file_path = await self.download_and_save_media(media_url, placeholder_message.id)
                    max_retries = 3
                    for _ in range(max_retries):
                        imgur_url = await self.upload_to_imgur(file_path)
                        if imgur_url:
                            embed_data["image_url"] = imgur_url
                            break
                        await asyncio.sleep(1)  # Wait for a second before retrying

                    if not imgur_url:
                        await self.reject_invalid_post(message, reason="Failed to upload to Imgur")
                        return
                    if valid_video:
                        await video_message.edit(content=imgur_url)
                        embed_data["image_url"] = ''
                        embed_data["description"] += f"\n\n[Watch Full Video Here!]({imgur_url})"

            # Delete the user's message and send a DM
            await message.delete()
            dm_embed_data = {
                "title": "Showcase Post Submitted",
                "description": "Your showcase post has been submitted to the admin for approval.",
                "color": discord.Color.blue()
            }
            dm_embed = await self.bot.get_cog("CreateEmbed").create_embed(**dm_embed_data)
            await message.author.send(embed=dm_embed)

            # Create the embed
            embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)

            # Instantiate your ApprovalButtons view
            approval_buttons_view = self.ApprovalButtons(self.bot, message, embed)

            if not is_youtube and not is_streamable:
                await placeholder_message.edit(content='', embed=embed, view=approval_buttons_view)
                if os.path.exists(file_path):
                    os.remove(file_path)

        except Exception as e:
            print(f"Error in on_message: {e}")
            await self.reject_invalid_post(message)

    async def reject_invalid_post(self, message: discord.Message) -> None:
        embed_data = {
            "title": "**Invalid Showcase Post**",
            "description": "Your showcase post must include media to be showcased with a description. Please try again. \
            If you believe this is an error, please contact an admin. \
            All submissions should contain LRD content and are subject to approval.",
            "color": discord.Color.red()
        }
        embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)
        await message.author.send(embed=embed)
        await message.delete()

    async def download_and_save_media(self, media_url, placeholder_message_id):
        media_directory = "./showcase"
        os.makedirs(media_directory, exist_ok=True)

        parsed_url = urllib.parse.urlparse(media_url)
        file_extension = os.path.splitext(parsed_url.path)[1]
        file_path = f"{media_directory}/{placeholder_message_id}{file_extension}"

        async with aiohttp.ClientSession() as session:
            async with session.get(media_url) as response:
                if response.status == 200:
                    with open(file_path, 'wb') as f:
                        f.write(await response.read())
        return file_path

async def setup(bot):
    await bot.add_cog(Showcase(bot))