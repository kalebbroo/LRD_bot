import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

# Load environment variables from .env file
load_dotenv()

bot = commands.Bot(command_prefix='!')


# Discord bot token
bot_token = os.getenv('DISCORD_BOT_TOKEN')


async def load_extensions():
    for filename in os.listdir('./core'):
        if filename.endswith('.py'):
            await bot.load_extension(f'core.{filename[:-3]}')

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    await load_extensions()
    fmt = await bot.tree.sync()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{bot.command_prefix}help"))
    print(f"synced {len(fmt)} commands")
    print(f"Loaded: {len(bot.cogs)} core files")


@bot.event
async def on_command_error(ctx, error):
    # handle your errors here
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"Command not found. Use {bot.command_prefix}help to see available commands.")
    else:
        print(f'Error occurred: {error}')


if __name__ == "__main__":
    bot.run(bot_token)
