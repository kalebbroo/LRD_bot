import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from core.welcome import RulesView

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

async def register_views(bot):
    guilds = bot.guilds
    for guild in guilds:
        guild_id = guild.id
        db_cog = bot.get_cog('Database')

        # For Showcase Messages
        showcase_cog = bot.get_cog('Showcase')
        if showcase_cog:
            message_ids = await db_cog.get_all_message_ids(guild_id)
            channel_info = await db_cog.get_channel_info(guild_id)
            channel_dict = {display_name: channel_id for display_name, channel_id in channel_info}
            for message_id in message_ids:
                channel_id = channel_dict.get("Showcase")
                if channel_id:
                    channel = bot.get_channel(channel_id)
                    message = await channel.fetch_message(message_id)
                    vote_buttons = showcase_cog.VoteButtons(bot, message)
                    await message.edit(view=vote_buttons)
        
        # For Support Messages
        support_cog = bot.get_cog('Support')
        if support_cog:
            support_channel_name = await db_cog.get_support_channel(guild_id)
            support_channel_id = await db_cog.get_id_from_display(guild_id, support_channel_name)
            if support_channel_id:
                support_channel = bot.get_channel(support_channel_id)
                support_message_id = await db_cog.get_message_id_from_channel(guild_id, "Support")  # Call the new method here
                if support_message_id:
                    support_message = await support_channel.fetch_message(support_message_id)
                    support_view = support_cog.TicketButton(bot, None)
                    await support_message.edit(view=support_view)

        # For Welcome Messages
        welcome_cog = bot.get_cog('WelcomeNewUser')
        if welcome_cog:
            welcome_channel_id = await db_cog.get_id_from_display(guild_id, 'Rules')
            #print(f"Welcome channel ID: {welcome_channel_id}")
            if welcome_channel_id:
                welcome_channel = bot.get_channel(welcome_channel_id)
                role_mapping, _ = await welcome_cog.get_role_mapping(guild_id)
                welcome_message_id = await db_cog.get_message_id_from_channel(guild_id, "Rules")
                welcome_message = await welcome_channel.fetch_message(welcome_message_id)
                # Edit the message view
                view = RulesView(bot, db_cog, guild_id, role_mapping)
                await welcome_message.edit(view=view)
            else:
                print("Welcome channel not found. Skipping.")
                await welcome_cog.bot_setup_message(guild_id)
        else:
            print("Welcome cog not found. Skipping.")

        print(f"Refreshed persistant buttons for guild {guild.name} with {bot.user.name}.")


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
    # handle your errors here
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Command not found. Use {bot.command_prefix}help to see available commands.")
    else:
        print(f'Error occurred: {error}')


if __name__ == "__main__":
    bot.run(bot_token)
