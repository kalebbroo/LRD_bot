import discord
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime, timedelta
import random
import asyncio
import io

class VoteView(View):
    def __init__(self, showcase_cog, post_id):
        super().__init__(timeout=None)
        self.showcase_cog = showcase_cog
        self.post_id = post_id
        self.add_item(VoteButton(self.showcase_cog, "Vote Up", "👍", "up", self.post_id))
        self.add_item(VoteButton(self.showcase_cog, "Vote Down", "👎", "down", self.post_id))

class VoteButton(Button):
    def __init__(self, showcase_cog, label, emoji, vote_type, post_id):
        super().__init__(style=discord.ButtonStyle.primary, label=label, emoji=emoji, custom_id=f"{vote_type}_{post_id}")
        self.post_id = post_id
        self.vote_type = vote_type
        self.showcase_cog = showcase_cog

    async def callback(self, interaction):
        # Handle vote using the Showcase cog's method
        vote_added = await self.showcase_cog.db.add_vote(self.post_id, interaction.user.id, self.vote_type)
        if not vote_added:
            await interaction.response.send_message(f"You've already voted on this post!", ephemeral=True)
            return
        await self.update_embed_with_votes(interaction.message, self.post_id)
        await interaction.response.send_message(f"Thanks for your vote!", ephemeral=True)
        if self.vote_type == "up":
            xp = 10  # You can adjust the XP value as needed
            await self.showcase_cog.bot.get_cog('XPCore').add_xp(interaction.user.id, interaction.guild.id, xp, interaction.channel.id)

    async def update_embed_with_votes(self, message, post_id):
        upvotes = await self.showcase_cog.db.get_vote_count_for_post(post_id, "up")
        downvotes = await self.showcase_cog.db.get_vote_count_for_post(post_id, "down")
        is_leader = await self.showcase_cog.db.is_leading_post(post_id)
        
        # Get the current embed from the message
        embed = message.embeds[0]
        
        # Update the footer with the new vote count
        leader_text = "🏆 Current Leader!" if is_leader else ""
        embed.set_footer(text=f"# of Upvotes: {upvotes} |⚖️| # of Downvotes: {downvotes} {leader_text}")
        
        # Edit the message with the updated embed
        await message.edit(embed=embed)

class ApprovalView(View):
    def __init__(self, showcase_cog, original_message, embed):
        super().__init__(timeout=None)
        self.showcase_cog = showcase_cog
        self.original_message = original_message
        self.embed = embed
        self.add_item(ApproveButton(self.showcase_cog, "Approve", "✅", self.original_message, self.embed))
        self.add_item(DenyButton(self.showcase_cog, "Deny", "🖕🏼", self.original_message))

class ApproveButton(Button):
    def __init__(self, showcase_cog, label, emoji, original_message, embed):
        super().__init__(style=discord.ButtonStyle.success, label=label, emoji=emoji, custom_id="approve")
        self.showcase_cog = showcase_cog
        self.original_message = original_message
        self.embed = embed

    async def callback(self, interaction):
        # Retrieve the showcase channel ID from the database
        showcase_channel_id = await self.showcase_cog.db.get_showcase_channel(interaction.guild.id)

        # Send the embed (with the image URL) to the showcase channel
        view = VoteView(self.showcase_cog, self.original_message.id)
        showcase_channel = self.showcase_cog.bot.get_channel(showcase_channel_id)
        showcase_post = await showcase_channel.send(embed=self.embed, view=view)

        # Open a thread on the embed that was posted in the showcase
        thread_name = f"Discussion for {self.original_message.author.name}'s post"
        await showcase_post.create_thread(name=thread_name, auto_archive_duration=1440)  # 1 day

        await interaction.response.send_message("Showcase approved!")

        # Award the user with random XP
        xp = random.randint(20, 100)
        await self.showcase_cog.bot.get_cog('XPCore').add_xp(self.original_message.author.id, self.original_message.guild.id, xp, self.original_message.channel.id)

class DenyButton(Button):
    def __init__(self, showcase_cog, label, emoji, original_message):
        super().__init__(style=discord.ButtonStyle.danger, label=label, emoji=emoji, custom_id="deny")
        self.showcase_cog = showcase_cog
        self.original_message = original_message

    async def callback(self, interaction):
        try:
            # Notify the user of the denial
            embed_data = {
            "title": "Showcase Post Denied",
            "description": "Your showcase post was denied by the admins. Please ensure it meets the following guidelines:",
            "color": discord.Color.red(),
            "fields": [
                {"name": "LittleRoomDev Content", "value": "The main purpose of this showcase channel is to showcase LittleRoomDev content you are using on your server."},
                {"name": "NSFW Content", "value": "Ensure there's no NSFW or inappropriate content in your post."},
                {"name": "Relevance", "value": "Make sure your post is relevant to the theme of the showcase channel."},
                {"name": "No Spam", "value": "Avoid spamming or posting duplicate content."},
                # Add more guidelines as needed...
            ],
            "footer": "Thank you for understanding!"
        }
            embed = await self.bot.get_cog("CreateEmbed").create_embed(**embed_data)
            await self.original_message.author.send(embed=embed)
            await interaction.response.send_message("Showcase denied!")
        except discord.errors.Forbidden:
            print("Couldn't send DM to user.")

class Showcase(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.get_cog("Database")

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
            await message.author.send("You can only post once every 24 hours in the showcase channel.", ephemeral=True)
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
            view = ApprovalView(self, message, embed)
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
            await message.channel.send("Error finding admin channel. Report this error to an Admin.", ephemeral=True)


    async def recreate_buttons(self, guild):
        showcase_channel_id = await self.db.get_showcase_channel(guild.id)
        if not showcase_channel_id:
            print(f"Failed to get showcase channel ID for guild {guild.name}")
            return

        showcase_channel = self.bot.get_channel(showcase_channel_id)

        # Get a limited number of past messages; you can adjust the limit if needed
        async for message in showcase_channel.history(limit=100):
            # Check if the message has an embed, indicating it's a showcase post
            if message.embeds:
                post_id = message.id
                # Create the VoteView with the buttons
                view = VoteView(self, post_id)
                # Edit the message to reattach the view with buttons
                await message.edit(view=view)
                # Sleep for a duration (e.g., 1 seconds) to avoid rate limits
                await asyncio.sleep(1)


async def setup(bot):
    await bot.add_cog(Showcase(bot))