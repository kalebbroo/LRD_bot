import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from core.welcome import RulesView
import asyncio

# Load environment variables from .env file
load_dotenv()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

# Discord bot token
bot_token = os.getenv('DISCORD_BOT_TOKEN')


async def load_extensions():
    for filename in os.listdir('./core'):
        if filename.endswith('.py'):
            await bot.load_extension(f'core.{filename[:-3]}')

async def register_views(bot: commands.Bot):
    # Fetch all guilds the bot is in
    guilds = bot.guilds
    for guild in guilds:
        guild_id = guild.id
        # Retrieve the Database cog
        db_cog = bot.get_cog('Database')
        
        # For Support Messages
        support_cog = bot.get_cog('Support')
        if support_cog:
            # Fetch support channel name from the Database
            support_channel_name = await db_cog.handle_channel(guild_id, "get_support_channel")
            # Fetch channel information from the Database
            channel_info = await db_cog.handle_channel(guild_id, "get_channel_info")
            # Convert the list of tuples to a dictionary for easier access
            channel_dict = {display_name.lower(): channel_id for display_name, channel_id in channel_info}
            # Fetch support channel ID using the dictionary
            support_channel_id = channel_dict.get(support_channel_name.lower()) if support_channel_name else None
            if support_channel_id:
                support_channel = bot.get_channel(support_channel_id)
                # Fetch support message ID from the Database
                support_message_id = await db_cog.handle_channel(guild_id, "get_message_id", display_name="Support")
                if support_message_id:
                    support_message = await support_channel.fetch_message(support_message_id)
                    support_view = support_cog.TicketButton(bot, None)
                    await support_message.edit(view=support_view)
            else:
                print(f"Support channel not found in {guild.name}. Skipping.")
                continue
        print(f"Refreshed persistent Support buttons for guild {guild.name} with {bot.user.name}.")

        # For Welcome Messages
        welcome_cog = bot.get_cog('WelcomeNewUser')
        if welcome_cog:
            # Fetch channel information from the Database
            channel_info = await db_cog.handle_channel(guild_id, "get_channel_info")
            # Convert the list of tuples to a dictionary for easier access
            channel_dict = {display_name.lower(): channel_id for display_name, channel_id in channel_info}
            # Fetch welcome channel ID using the dictionary
            welcome_channel_id = channel_dict.get('rules')
            if welcome_channel_id:
                welcome_channel = bot.get_channel(welcome_channel_id)
                # Fetch role mapping from the Database
                role_mapping, _ = await welcome_cog.get_role_mapping(guild_id)
                # Fetch welcome message ID from the Database
                welcome_message_id = await db_cog.handle_channel(guild_id, "get_message_id", display_name="Rules")
                if welcome_message_id:
                    welcome_message = await welcome_channel.fetch_message(welcome_message_id)
                    # Edit the message view
                    view = RulesView(bot, db_cog, guild_id, role_mapping)
                    await welcome_message.edit(view=view)
                else:
                    print(f"Welcome message not found in {guild.name}. Skipping.")
            else:
                print(f"Welcome channel not found in {guild.name}. Skipping.")
                await welcome_cog.setup_message(guild_id)
        else:
            print(f"Welcome cog not found in {guild.name}. Skipping.")

        print(f"Refreshed persistent Welcome buttons for guild {guild.name} with {bot.user.name}.")

        # For Showcase Messages
        showcase_cog = bot.get_cog('Showcase')
        if showcase_cog:
            # Fetch all message IDs for the showcase from the Database
            message_ids = await db_cog.handle_showcase(guild_id, "get_all_message_ids")
            num_messages = len(message_ids) # number of messages in the showcase

            edits_per_period = 5 # number of edits per period
            period_duration = 20  # in seconds
            # Calculate total time needed to edit all messages without hitting rate limits
            total_time_for_edits = (num_messages / edits_per_period) * period_duration

            # Calculate average sleep time between each edit
            if num_messages > 0: # avoid division by zero
                sleep_time = total_time_for_edits / num_messages
            else:
                sleep_time = 0  # default value

            # Fetch channel information from the Database
            channel_info = await db_cog.handle_channel(guild_id, "get_channel_info")
            channel_dict = {display_name: channel_id for display_name, channel_id in channel_info}
            for message_id in message_ids: # loop through all messages
                channel_id = channel_dict.get("Showcase")
                
                if channel_id:
                    channel = bot.get_channel(channel_id)
                    try:
                        await asyncio.sleep(sleep_time) # Dynamic sleep time to avoid rate limit
                        message = await channel.fetch_message(message_id)
                        vote_buttons = showcase_cog.VoteButtons(bot)
                        await message.edit(view=vote_buttons) # Refresh the buttons
                    except discord.errors.NotFound:
                        print(f"Message {message_id} not found in channel {channel_id}. Removing from the database.")
                        await db_cog.handle_showcase(guild_id, "remove_message", message_id=message_id)
                        continue
                else:
                    print(f"Showcase channel not found in {guild.name}. Skipping.")
                    continue
        print(f"Refreshed persistent Showcase buttons for guild {guild.name} with {bot.user.name}.")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    await load_extensions()
    fmt = await bot.tree.sync()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"/help"))
    print(f"synced {len(fmt)} commands")
    print(f"Loaded: {len(bot.cogs)} core files")

    # Call the register_views function
    await register_views(bot)


@bot.event
async def on_command_error(ctx, error):
    # handle command errors here
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Command not found. Use {bot.command_prefix}help to see available commands.")
    else:
        print(f'Error occurred: {error}')


if __name__ == "__main__":
    bot.run(bot_token)
