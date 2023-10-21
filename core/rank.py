import discord
from discord.ext import commands
from discord import app_commands
from DiscordLevelingCard import RankCard, Settings, Sandbox
from PIL import Image
from io import BytesIO
import requests

class RankCore(commands.Cog):
    """
    Cog responsible for managing and displaying user ranks in the server.
    """
    def __init__(self, bot):
        """Initialize the RankCore with the bot object and database cog."""
        self.bot = bot
        self.db_cog = self.bot.get_cog('Database')

    @app_commands.command(name='rank', description='Check a user\'s rank')
    @app_commands.describe(member='The member to check the rank of')
    async def rank(self, interaction, member: discord.Member = None):
        """
        Display the rank card for a specified user or the invoking user if no user is specified.
        """
        try:
            await interaction.response.defer()
            if member is None:
                member = interaction.user  # If no member is specified, use the user who invoked the command

            user_id = member.id
            db_cog = self.bot.get_cog('Database')
            user = await db_cog.get_user(user_id, interaction.guild.id)
            if user is None:
                user = {
                    'id': user_id,
                    'guild_id': interaction.guild.id,
                    'xp': 0,
                    'level': 0,
                    'last_message_time': 0,
                    'spam_count': 0,
                    'warnings': 0,
                    'message_count': 0,
                    'last_warn_time': None,
                    'emoji_count': 0,
                    'name_changes': 0,
                    'last_showcase_post': None
                }
                await db_cog.update_user(user, interaction.guild.id)
        except requests.RequestException:
            await interaction.followup.send("Error fetching images for rank card.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
            return

        xp = user['xp']
        level = user['level']
        xp_to_next_level = round(((1.2 ** (level + 1) - 1) * 100) / 0.2) 
        rank = await db_cog.get_rank(user_id, interaction.guild.id)

        card_settings = Settings(
            background="https://cdn.discordapp.com/attachments/1122904665986711622/1122904935923716187/bg.jpg",
            text_color="white",
            bar_color="#800080"
        )
        card = RankCard(
            settings=card_settings,
            username=member.display_name,
            avatar=member.avatar.url,
            level=level,
            rank=rank,
            current_exp=xp,
            max_exp=xp_to_next_level
        )
        image = await card.card3()  # Generate the card image
        file = discord.File(fp=image, filename='image.png')
        await interaction.followup.send(file=file)


    @app_commands.command(name='user_stats', description='Display user stat card')
    @app_commands.describe(member='The member to view stats of')
    async def user_stats(self, interaction, member: discord.Member):
        """
        Display statistics for a given member in the server.
        """
        try:
            await interaction.response.defer()
            db_cog = self.bot.get_cog('Database')
            user = await db_cog.get_user(member.id, interaction.guild.id)

            setting = Settings(
                background="https://cdn.discordapp.com/attachments/1122904665986711622/1123091340008370228/wumpus.jpg",
                bar_color="green",
                text_color="white"
            )
            stats_card = Sandbox(
                username=member.display_name,
                level=user['level'],
                current_exp=user['xp'],
                max_exp = round(((1.2 ** (user['level'] + 1) - 1) * 100) / 0.2),
                settings=setting,
                avatar=member.avatar.url
            )
            result = await stats_card.custom_canvas(
                avatar_frame="square",
                avatar_size=233,
                avatar_position=(50, 50),
                exp_bar_background_colour="black",
                exp_bar_height=50,
                exp_bar_width=560,
                exp_bar_curve=0,
                exp_bar_position=(70, 400),
                username_position=(320, 50),
                level_position=(320, 225),
                exp_position=(70, 330),
                canvas_size=(700, 500),
                overlay=[
                    [(350, 233), (300, 50), "white", 100],
                    [(600, 170), (50, 300), "white", 100]
                ],
                extra_text=[
                    ["Roles: " + str(len(member.roles)), (320, 110), 25, "white"],
                    ["Messages: " + str(user['message_count']), (320, 140), 25, "white"],
                    ["Emoji: " + str(user['emoji_count']), (320, 170), 25, "white"],
                    ["Highest Role: " + str(member.top_role), (320, 200), 25, "white"],
                ]
            )
            file = discord.File(fp=result, filename='user_stats.png')
            await interaction.followup.send(file=file)
        except requests.RequestException:
            await interaction.followup.send("Error fetching images for user stats card.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)


    # @app_commands.command(name='server_stats', description='Display server stats')
    # async def server_stats(self, interaction):
    #     await interaction.response.defer()

    #     extra_text = [
    #         ["Members:", (320, 110), 25, "white"],
    #         [str(interaction.guild.member_count), (320, 140), 25, "white"],
    #         ["Channels:", (320, 170), 25, "white"],
    #         [str(len(interaction.guild.channels)), (320, 200), 25, "white"],
    #         ["Roles:", (320, 230), 25, "white"],
    #         [str(len(interaction.guild.roles)), (320, 260), 25, "white"],
    #     ]
    #     # Generate the card
    #     result = await self.generate_card(interaction.guild.name, interaction.guild.icon.url, None, None, None, extra_text)

    #     # Send the card
    #     file = discord.File(fp=result, filename='server_stats.png')
    #     await interaction.followup.send(file=file)


    async def level_up(self, user_id, guild_id, channel_id):
        """
        Announce the level up for a user and display their new rank card.
        """
        try:
            db_cog = self.bot.get_cog('Database')
            user = await db_cog.get_user(user_id, guild_id)
            guild = self.bot.get_guild(guild_id)
            member = guild.get_member(user_id)
            if user['level'] == 2:
                role = discord.utils.get(guild.roles, name="Not Silent")
                if role:
                    await member.add_roles(role)
                    print(f"Assigned role 'Not Silent' to {member.name}.")
                else:
                    print("Role 'Not Silent' not found.")
                 
            # Check if the user is below level 5
            if user['level'] < 5:
                return

            # If user is between levels 5-15, send the card to bot-spam channel
            if 5 <= user['level'] <= 15:
                channel = discord.utils.get(guild.text_channels, name="bot-spam")
            else:
                channel = self.bot.get_channel(channel_id)

            setting = Settings(
                background="https://cdn.discordapp.com/attachments/1122904665986711622/1123091340008370228/wumpus.jpg",
                bar_color="green",
                text_color="white"
            )
            rank = Sandbox(
                username=member.display_name,
                level=user['level'],
                current_exp=user['xp'],
                max_exp = round(((1.2 ** (user['level'] + 1) - 1) * 100) / 0.2),
                settings=setting,
                avatar=member.avatar.url
            )
            result = await rank.custom_canvas(
                avatar_frame="square",
                avatar_size=233,
                avatar_position=(50, 50),
                exp_bar_background_colour="black",
                exp_bar_height=50,
                exp_bar_width=560,
                exp_bar_curve=0,
                exp_bar_position=(70, 400),
                username_position=(320, 50),
                level_position=(320, 225),
                exp_position=(70, 330),
                canvas_size=(700, 500),
                overlay=[
                    [(350, 233), (300, 50), "white", 100],
                    [(600, 170), (50, 300), "white", 100]
                ],
                extra_text=[
                    ["Level Up!", (320, 110), 25, "white"],
                    [f"Congratulations {member.display_name}!", (320, 140), 25, "white"],
                    [f"You've leveled up to level {user['level']}!", (320, 170), 25, "white"],
                    [f"User: {member.display_name}", (320, 200), 25, "white"],
                ]
            )
            file = discord.File(fp=result, filename='level_up.png')
            await channel.send(file=file)
        except requests.RequestException:
            await channel.send("Error fetching images for level up card.")
        except Exception as e:
            await channel.send(f"An error occurred: {str(e)}")

    async def generate_card(self, username, avatar, level, current_exp, max_exp, extra_text, **kwargs):
        """
        Generate a custom rank card based on the provided user information and settings.
        """
        try:
            off_canvas = (-100, -100)  # Position off the canvas
            # Default settings and conditions
            settings = {
                "avatar_frame": ("square", True),
                "avatar_size": (233, True),
                "avatar_position": ((50, 50), True),
                "exp_bar_background_colour": ("black", current_exp is not None and max_exp is not None),
                "exp_bar_height": (50, current_exp is not None and max_exp is not None),
                "exp_bar_width": (560, current_exp is not None and max_exp is not None),
                "exp_bar_curve": (0, current_exp is not None and max_exp is not None),
                "exp_bar_position": ((70, 400), current_exp is not None and max_exp is not None),
                "username_position": ((320, 50), True),
                "level_position": (off_canvas if level is None else (320, 225)),
                "exp_position": (off_canvas if current_exp is None or max_exp is None else (70, 330)),
                "canvas_size": ((700, 500), True),
                "overlay": ([[(350, 233),(300, 50), "white", 100], [(600, 170),(50, 300), "white", 100]], True),
            }
            # Update settings with any arguments passed in
            for key, (default, condition) in settings.items():
                if key not in kwargs and condition:
                    kwargs[key] = default

            # Settings for the card
            setting = Settings(
                background="https://cdn.discordapp.com/attachments/1122904665986711622/1123091340008370228/wumpus.jpg",
                bar_color="green",
                text_color="white"
            )
            # Create the rank card
            if level is None:
                level = 0
            if current_exp is None:
                current_exp = 0
            if max_exp is None:
                max_exp = 0

            card = Sandbox(
                username=username,
                level=level,
                current_exp=current_exp,
                max_exp=max_exp,
                settings=setting,
                avatar=avatar
            )
            # Generate the card
            result = await card.custom_canvas(**kwargs, extra_text=extra_text)
            return result
        except Exception as e:
            raise Exception(f"An error occurred in generating the card: {str(e)}")

    async def generate_user_card(self, member, rank, level, xp, message_count, emoji_count):
        """
        Generate a detailed user card displaying various stats for a user.
        """
        try:
            off_canvas = (-100, -100)  # Position off the canvas
            current_exp = None
            max_exp = None

            settings = {
                "avatar_frame": ("square", True),
                "avatar_size": (233, True),
                "avatar_position": ((50, 50), True),
                "exp_bar_background_colour": ("black", current_exp is not None and max_exp is not None),
                "exp_bar_height": (50, current_exp is not None and max_exp is not None),
                "exp_bar_width": (560, current_exp is not None and max_exp is not None),
                "exp_bar_curve": (0, current_exp is not None and max_exp is not None),
                "exp_bar_position": ((70, 400), current_exp is not None and max_exp is not None),
                "username_position": ((320, 50), True),
                "level_position": off_canvas if level is None else (320, 225),
                "exp_position": (off_canvas if current_exp is None or max_exp is None else (70, 330)),
                "canvas_size": ((700, 500), True),
                "overlay": ([[(350, 233),(300, 50), "white", 100], [(600, 170),(50, 300), "white", 100]], True),
            }
            kwargs = {}
            # Update settings with any arguments passed in
            for key, (default, condition) in settings.items():
                if condition:
                    kwargs[key] = default

            setting = Settings(
                background="https://cdn.discordapp.com/attachments/1122904665986711622/1123091340008370228/wumpus.jpg",
                bar_color="green",
                text_color="white"
            )
            username = member.name
            avatar = str(member.avatar.url)

            # Add extra_text as required
            extra_text = [
                ["Rank: " + str(rank), (320, 225)],
                ["Messages: " + str(message_count), (320, 275)],
                ["Emojis: " + str(emoji_count), (320, 325)]
            ]
            # Create the rank card
            if level is None:
                level = 0
            if current_exp is None:
                current_exp = 0
            if max_exp is None:
                max_exp = 0

            card = Sandbox(
                username=username,
                level=level,
                current_exp=xp,
                max_exp=1000000000,  # You can modify this to the actual maximum experience value if you have one
                settings=setting,
                avatar=avatar
            )
            result = await card.custom_canvas(**kwargs, extra_text=extra_text)
            return result
        except Exception as e:
            raise Exception(f"An error occurred in generating the user card: {str(e)}")

    # @app_commands.command(name='leaderboard', description='Display the server leaderboard')
    # async def leaderboard(self, interaction):
    #     await interaction.response.defer()
    #     guild_id = interaction.guild.id
    #     self.db_cog = self.bot.get_cog('Database')
    #     users = await self.db_cog.get_top_users(guild_id, 10)

    #     image_url = "https://cdn.discordapp.com/attachments/1122904665986711622/1123091340008370228/wumpus.jpg"
    #     response = requests.get(image_url, stream=True)
    #     response.raw.decode_content = True  # Ensures that gzip content is decoded

    #     canvas = Image.open(response.raw).convert("RGBA")  # Load the background image
    #     overlay = Image.new('RGBA', canvas.size)  # Create a new overlay with the same size as the background

    #     # Generate a card for each user and paste it onto the canvas
    #     x, y = 0, 0  # Initialize the x, y-coordinates
    #     for i, user in enumerate(users):
    #         try:
    #             member = await self.bot.get_guild(guild_id).fetch_member(user['id'])
    #             card_bytes = await self.generate_user_card(
    #             member=member,
    #             rank=i+1,
    #             level=user['level'],
    #             xp=user['xp'],
    #             message_count=user['message_count'],
    #             emoji_count=user['emoji_count']
    #         )
    #             # Convert the card bytes to a PIL Image
    #             card = Image.open(BytesIO(card_bytes))
    #             overlay.paste(card, (x, y))  # Paste the card onto the overlay

    #             # Update the coordinates
    #             if i == 4:  # After 5 users, move to the right column and reset the y-coordinate
    #                 x += card.width
    #                 y = 0
    #             else:
    #                 y += card.height
    #         except discord.NotFound:
    #             continue

    #     # Composite the background and overlay
    #     canvas = Image.alpha_composite(canvas, overlay)

    #     # Save the canvas to a BytesIO object
    #     output = BytesIO()
    #     canvas.save(output, format='PNG')
    #     output.seek(0)

    #     # Send the canvas
    #     file = discord.File(fp=output, filename='leaderboard.png')
    #     await interaction.followup.send(file=file)

async def setup(bot):
    """Load the RankCore cog."""
    await bot.add_cog(RankCore(bot))
