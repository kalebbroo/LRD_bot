import discord
from discord.ext import commands
from discord import app_commands, Member, Interaction
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

    @app_commands.command(name='rank', description='Check a user\'s rank')
    @app_commands.describe(member='The member to check the rank of')
    async def rank(self, interaction: Interaction, member: Member = None) -> None:
        """
        Display the rank card for a specified user or the invoking user if no user is specified.
        """
        try:
            await interaction.response.defer()
            self.db = self.bot.get_cog('Database')
            if member is None:
                member = interaction.user  # If no member is specified, use the user who invoked the command

            # Fetching user data from updated Database cog
            user = await self.db.handle_user(interaction.guild.id, "get", user_id=member.id)
            if user is None:
                # Initialize user data if not found in the database
                user = {
                    'id': member.id,
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
                await self.db.handle_user(interaction.guild.id, "update", user_id=member.id, user_data=user)

        except requests.RequestException:
            await interaction.followup.send("Error fetching images for rank card.", ephemeral=True)
            print("Error fetching images for rank card.")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
            print(f"An error occurred: {str(e)}")
            return

        # Calculate xp, level, and rank
        xp = user['xp']
        level = user['level']
        xp_to_next_level = round(((1.2 ** (level + 1) - 1) * 100) / 0.2)
        rank = await self.db.handle_user(interaction.guild.id, "get_rank", user_id=member.id)
        local_image_path = "./images/rank_upscale.png" 

        card_settings = Settings(
            background=local_image_path,
            text_color="black",
            bar_color="#00008B"
        )
        rank_card = Sandbox(
                username=member.display_name,
                level=user['level'],
                current_exp=user['xp'],
                max_exp = round(((1.2 ** (user['level'] + 1) - 1) * 100) / 0.2),
                settings=card_settings,
                avatar=member.avatar.url
            )
        result = await rank_card.custom_canvas(
                avatar_frame="square",
                avatar_size=250,
                avatar_position=(258, 0),
                exp_bar_background_colour="black",
                exp_bar_height=30,
                exp_bar_width=715,
                exp_bar_curve=20,
                exp_bar_position=(25, 387),
                username_position=(265, 245),
                username_font_size=70,
                level_position=(800, 200),
                level_font_size=50,
                exp_position=(540, 340),
                exp_font_size=40,
                canvas_size=(768, 440),
                overlay=[
                    #[(350, 233), (300, 50), "black", 100],
                    #[(280, 50), (20, 328), "black", 100]  # Size (width, height), Position (x, y), Color, Opacity
                ],
                extra_text=[
                    # Adjust the positions and potentially the font size for these texts
                    ["Roles: " + str(len(member.roles)), (20, 350), 30, "#D3D3D3"],
                    ["Messages: " + str(user['message_count']), (20, 320), 30, "#D3D3D3"],
                    ["Emoji: " + str(user['emoji_count']), (185, 320), 30, "#D3D3D3"],
                    ["Highest Role: " + str(member.top_role), (120, 350), 30, "#D3D3D3"],
                    ["Level: " + str(user['level']), (560, 210), 38, "white"],
                ]
            )
        file = discord.File(fp=result, filename='user_stats.png')
        await interaction.followup.send(file=file)


    # @app_commands.command(name='user_stats', description='Display user stat card')
    # @app_commands.describe(member='The member to view stats of')
    # async def user_stats(self, interaction: Interaction, member: Member) -> None:
    #     """
    #     Display statistics for a given member in the server.
    #     """
    #     try:
    #         await interaction.response.defer()
    #         # Fetching user data from the updated Database cog
    #         user = await self.db.handle_user(interaction.guild.id, "get", user_id=member.id)
    #         if user is None:
    #             await interaction.followup.send("User data not found.", ephemeral=True)
    #             return
            
    #         setting = Settings(
    #             background="https://cdn.discordapp.com/attachments/1122904665986711622/1123091340008370228/wumpus.jpg",
    #             bar_color="green",
    #             text_color="white"
    #         )
    #         stats_card = Sandbox(
    #             username=member.display_name,
    #             level=user['level'],
    #             current_exp=user['xp'],
    #             max_exp = round(((1.2 ** (user['level'] + 1) - 1) * 100) / 0.2),
    #             settings=setting,
    #             avatar=member.avatar.url
    #         )
    #         result = await stats_card.custom_canvas(
    #             avatar_frame="square",
    #             avatar_size=233,
    #             avatar_position=(50, 50),
    #             exp_bar_background_colour="black",
    #             exp_bar_height=50,
    #             exp_bar_width=560,
    #             exp_bar_curve=0,
    #             exp_bar_position=(70, 400),
    #             username_position=(320, 50),
    #             level_position=(320, 225),
    #             exp_position=(70, 330),
    #             canvas_size=(700, 500),
    #             overlay=[
    #                 [(350, 233), (300, 50), "white", 100],
    #                 [(600, 170), (50, 300), "white", 100]
    #             ],
    #             extra_text=[
    #                 ["Roles: " + str(len(member.roles)), (320, 110), 25, "white"],
    #                 ["Messages: " + str(user['message_count']), (320, 140), 25, "white"],
    #                 ["Emoji: " + str(user['emoji_count']), (320, 170), 25, "white"],
    #                 ["Highest Role: " + str(member.top_role), (320, 200), 25, "white"],
    #             ]
    #         )
    #         file = discord.File(fp=result, filename='user_stats.png')
    #         await interaction.followup.send(file=file)
    #     except requests.RequestException:
    #         await interaction.followup.send("Error fetching images for user stats card.", ephemeral=True)
    #     except Exception as e:
    #         await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)

    async def level_up(self, user_id, guild_id, channel_id):
        """
        Announce the level up for a user and display their new rank card.
        """
        showcase_channel_id = await self.bot.get_cog('Database').handle_channel(guild_id, "get_showcase_channel")
        # If the channel is the showcase channel, don't post the level-up message
        if channel_id == showcase_channel_id:
            return
        try:
            # Fetching user data from the updated Database cog
            user = await self.db_cog.handle_user(guild_id, "get", user_id=user_id)
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
