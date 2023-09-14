import discord
from discord.ext import commands, tasks
from discord import app_commands, Embed, Colour
from discord.ui import Modal, TextInput, Select
from discord.app_commands import Choice
from datetime import datetime
import asyncio
import random
import time
import math

"""
Ways to Earn XP:
1. Sending Messages:
   - Base XP: Random between 5-50.
   - Modifiers: Double XP Day (2x), Active User Reward (+20%).
   
2. Adding Reactions:
   - Base XP: 1 XP per reaction.
   - Penalty: -100 XP for spamming reactions.
   - Modifiers: Emoji Madness (10x).

3. Streaming in Voice Channels:
   - Base XP: 10 XP for starting a stream.
   - Extra: +5 XP every 10 minutes if at least 4 viewers.
   - Modifiers: Voice Chat Vibes (+50%).

4. Using Slash Commands:
   - Base XP: random XP between 5-50.
   - Modifiers: Playing With Bots (+10%).
"""

class XPCore(commands.Cog):
    """
    Cog responsible for managing user XP in the server.
    """
    def __init__(self, bot:commands.Bot):
        """Initialize the XPCore with the bot object and other initial settings."""
        try:
            self.bot = bot
            self.db_cog = self.bot.get_cog('Database')  # Database cog instance
            self.voice_channels = {}  # Store voice channel states
            self.stream_check_task = None  # Task for checking streams
            self.xp_bonus = XPBonus()  # XP bonus object
            self.current_event = None  # Current event, if any
            self.event_start_time = None  # Start time of the current event
            self.last_reaction_time = {}  # Store last reaction times to detect spamming
        except Exception as e:
            print(f"Error in __init__: {e}")

    async def add_xp(self, user_id, guild_id, xp, channel_id):
        """
        Add XP to a user and update the user's XP in the database.
        """
        try:
            user = await self.db_cog.get_user(user_id, guild_id)
            if self.current_event is not None and self.current_event['name'] == "Double XP Day":
                xp = self.current_event['bonus'](xp)
            user['xp'] += xp
            user['xp'] = round(user['xp'])
            count = user['message_count']
            name = self.bot.get_user(user_id).display_name
            level = 1
            while user['xp'] >= ((1.2 ** level - 1) * 100) / 0.2:
                level += 1
            if level > user['level']:
                user['level'] = level
                await self.bot.get_cog('RankCore').level_up(user_id, guild_id, channel_id)
            next_level_xp = ((1.2 ** (user['level'] + 1) - 1) * 100) / 0.2
            xp_to_next_level = math.ceil(next_level_xp - user['xp'])
            print(f"{name} has {user['xp']} XP and is at level {user['level']}. They just gained {xp} XP.")
            print(f"They need {xp_to_next_level} more XP to level up. They have sent {count} messages.")
            await self.db_cog.update_user(user, guild_id)
        except Exception as e:
            print(f"Error in add_xp: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Listener to handle when a message is sent. Add XP to the user.
        """
        try:
            if message.author.bot:
                return
            user_id = message.author.id
            guild_id = message.guild.id
            user = await self.db_cog.get_user(user_id, guild_id)
            if user is None:
                print(f"user was a bot or not in the database")
                return 
            xp = random.randint(5, 50)
            print(f"Adding {xp} XP to user {user_id}")
            await self.add_xp(user_id, guild_id, xp, message.channel.id)
            updated_user = await self.db_cog.get_user(user_id, guild_id)
            print(f"User {user_id} now has {updated_user['xp']} XP")
        except Exception as e:
            print(f"Error in on_message: {e}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """
        Listener to handle when a reaction is added. Add XP to the user.
        """
        try:
            if user == self.bot.user:
                return
            user_id = user.id
            guild_id = reaction.message.guild.id
            user = await self.db_cog.get_user(user_id, guild_id)
            user['emoji_count'] += 1  # Increment emoji count
            if user_id not in self.last_reaction_time:
                self.last_reaction_time[user_id] = -math.inf
            if time.time() - self.last_reaction_time[user_id] < 0.5:  # If the user is spamming reactions
                user['xp'] -= 100  # Remove 100 XP
                await reaction.message.channel.send(f"{user.mention} Stop spamming reactions! 100 XP has been deducted from your total.", ephemeral=True)
            self.last_reaction_time[user_id] = time.time()
            await self.db_cog.update_user(user, guild_id)
            xp = 1  # Define xp before using it
            if self.current_event is not None and self.current_event['name'] == "Emoji Madness":
                xp = self.current_event['bonus'](xp)
            await self.add_xp(user_id, guild_id, xp, reaction.message.channel.id)  # Add 1 XP for the reaction
        except Exception as e:
            print(f"Error in on_reaction_add: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        Listener to handle voice state updates. Handle XP when a user joins or leaves a voice channel.
        """
        try:
            xp = 10  # Set a base XP value
            if self.current_event is not None and self.current_event['name'] == "Voice Chat Vibes":
                xp = self.current_event['bonus'](xp)
            if not before.self_stream and after.self_stream:  # The member started streaming
                user_id = member.id
                guild_id = member.guild.id
                channel_id = after.channel.id
                self.voice_channels[channel_id] = {'streamer': user_id, 'watchers': []}  # Initialize the channel state
                await self.add_xp(user_id, guild_id, 10, channel_id)  # Add 10 XP for starting a stream
                if self.stream_check_task is None:  # If the background task is not running
                    self.stream_check_task = self.bot.loop.create_task(self.check_streams())  # Start the background task
            elif before.self_stream and not after.self_stream:  # The member stopped streaming
                channel_id = before.channel.id
                if channel_id in self.voice_channels:  # Remove the channel state
                    del self.voice_channels[channel_id]
                if not self.voice_channels and self.stream_check_task is not None:  # If no one is streaming
                    self.stream_check_task.cancel()  # Stop the background task
                    self.stream_check_task = None
            else:  # The member joined or left a voice channel
                if before.channel is not None:
                    channel_id = before.channel.id
                    if channel_id in self.voice_channels:  # Update the list of watchers
                        channel = self.bot.get_channel(channel_id)
                        self.voice_channels[channel_id]['watchers'] = [member.id for member in channel.members if not member.bot and not member.voice.self_stream]
                if after.channel is not None:
                    channel_id = after.channel.id
                    if channel_id in self.voice_channels:  # Update the list of watchers
                        channel = self.bot.get_channel(channel_id)
                        self.voice_channels[channel_id]['watchers'] = [member.id for member in channel.members if not member.bot and not member.voice.self_stream]
                xp = 0
                if self.current_event is not None and self.current_event['name'] == "Voice Chat Vibes":
                    xp = self.current_event['bonus'](xp)
                if after.channel is not None:
                    await self.add_xp(member.id, member.guild.id, xp, after.channel.id)
        except Exception as e:
            print(f"Error in on_voice_state_update: {e}")

    async def check_streams(self):
        """
        Background task to check active voice streams and award XP to streamers.
        """
        try:
            while True:
                for channel_id, state in list(self.voice_channels.items()):  # Iterate over a copy of the dictionary
                    if len(state['watchers']) >= 4:  # If there are at least 2 watchers
                        await self.add_xp(state['streamer'], self.bot.get_channel(channel_id).guild.id, 5, channel_id)  # Add 5 XP to the streamer
                await asyncio.sleep(600)  # Wait for 10 minutes
        except Exception as e:
            print(f"Error in check_streams: {e}")

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        """
        Listener to handle interactions. Add XP for specific interactions.
        """
        try:
            #print(f"type: {interaction.type}")
            if interaction.type == discord.InteractionType.application_command:
                #print(f"interaction was a slash command")
                user_id = interaction.user.id
                guild_id = interaction.guild.id

                # Generate a random amount of XP for using a slash command
                xp = random.randint(5, 50)  # Adjust the range as needed

                print(f"Adding {xp} XP to user {user_id} for using a slash command")
                await self.add_xp(user_id, guild_id, xp, interaction.channel.id)
                user = await self.db_cog.get_user(user_id, guild_id)  # Get the user from the database
                await self.db_cog.update_user(user, guild_id)  # Update the user in the database
        except Exception as e:
            print(f"Error in on_interaction: {e}")

    @app_commands.command(name='bonus_xp_event', description='Trigger an XP bonus event.')
    @app_commands.choices(event_name=[
        Choice(name='Double XP Day', value="Double XP Day"),
        Choice(name='Playing With Bots', value="Playing With Bots"),
        Choice(name='Active User Reward', value="Active User Reward"),
        Choice(name='Emoji Madness', value="Emoji Madness"),
        Choice(name='Voice Chat Vibes', value="Voice Chat Vibes"),
        Choice(name='Random', value="random")
    ])
    async def trigger_event(self, interaction, event_name: str):
        await interaction.response.defer()
        if self.event_task and self.event_task.is_running():
            self.event_task.cancel()
        try:
            # If event is random, choose a random event
            if event_name == "random":
                self.current_event = random.choice(self.xp_bonus.event)
            else:
                self.current_event = next((event for event in self.xp_bonus.event if event['name'] == event_name), None)
            
            if not self.current_event:
                await interaction.followup.send("No such event found!", ephemeral=True)
                return

            self.event_start_time = datetime.now()

            guild_id = interaction.guild.id
            await self.announce_event(guild_id)

            # Schedule the task to reset the event after its duration
            self.event_task = tasks.Loop(seconds=self.current_event['duration'] * 3600, count=1)(self.reset_event)
            self.event_task.start(guild_id)

        except Exception as e:
            print(f"Error in trigger_event command: {e}")
            error_embed = await self.embed_cog.create_embed(
                title="Error",
                description="An error occurred while processing your request.",
                color=Colour.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @tasks.loop(hours=1)  # This will actually be overridden by the above
    async def reset_event(self, guild_id):
        """Reset the current event after its duration."""
        self.current_event = None
        self.event_start_time = None
        await self.db_cog.set_bot_channel(guild_id)  # Set the bot channel
        bot_channel = self.db_cog.get_bot_channel(guild_id)  # Get the bot channel
        await bot_channel.send("The XP event has ended! XP rates are back to normal.")


    async def announce_event(self, guild_id):
        try:
            event = self.current_event
            embed = discord.Embed(title=event['name'], description=event['description'], color=0x00ff00)
            embed.add_field(name="Duration", value=f"{event['duration']} hours", inline=False)
            embed.add_field(name="Bonus", value=f"{event['bonus'](1)}x XP", inline=False)
            self.bot_channel = await self.db_cog.set_bot_channel(guild_id)  # Set the bot channel
            await self.bot_channel.send(embed=embed)
        except Exception as e:
            print(f"Error in announce_event: {e}")


class XPBonus:
    """
    Class for managing various XP bonus events.
    """
    def __init__(self):
        """Initialize the XPBonus class with a list of events."""
        try:
            self.event = [
                {
                    "name": "Double XP Day",
                    "description": "Earn double XP for the next 8 hours!",
                    "bonus": lambda xp: xp * 2,
                    "duration": 8  # hours
                },
                {
                    "name": "Playing With Bots",
                    "description": "Earn 10% more XP for every bot command used in the next 8 hours!",
                    "bonus": lambda xp: xp * 1.1,
                    "duration": 8  # hour
                },
                {
                    "name": "Active User Reward",
                    "description": "Earn 20% more XP for every message sent in the next 3 hours!",
                    "bonus": lambda xp: xp * 1.2,
                    "duration": 3  # hours
                },
                {
                    "name": "Emoji Madness",
                    "description": "Earn 10x XP for every emoji in the next 2 hours! Spamming will result in a SEVERE reduction of xp!",
                    "bonus": lambda xp: xp * 10,
                    "duration": 2  # hours
                },
                {
                    "name": "Voice Chat Vibes",
                    "description": "Earn bonus XP for participating in a voice chat in the next 8 hours!",
                    "bonus": lambda xp: xp * 1.5,
                    "duration": 4  # hours
                }
                # {
                #     "name": "Weekend Warrior",
                #     "description": "Earn 25% more XP for all activities during the weekend!",
                #     "bonus": lambda xp: xp * 1.25,
                #     "duration": 48  # hours
                # },
                # {
                #     "name": "Channel Explorer",
                #     "description": "Earn double XP for posting in a new channel in the next hour!",
                #     "bonus": lambda xp: xp * 2,
                #     "duration": 1  # hour
                # },
                # {
                #     "name": "Roleplay Bonus",
                #     "description": "Earn triple XP for participating in roleplay in the next 2 hours!",
                #     "bonus": lambda xp: xp * 3,
                #     "duration": 2  # hours
                # },
                # {
                #     "name": "Art Appreciation",
                #     "description": "Earn double XP for posting or reacting to art in the next 3 hours!",
                #     "bonus": lambda xp: xp * 2,
                #     "duration": 3  # hours
                # },
                # {
                #     "name": "Helping Hand",
                #     "description": "Earn 50% more XP for helping other users in the next hour!",
                #     "bonus": lambda xp: xp * 1.5,
                #     "duration": 1  # hour
                # }
                # {
                #     "name": "Night Owl",
                #     "description": "Earn 50% more XP for activities done at night (6PM - 12AM)!",
                #     "bonus": lambda xp: xp * 1.5,
                #     "duration": 6  # hours
                # },
                # {
                #     "name": "Trivia Time",
                #     "description": "Earn triple XP for participating in trivia in the next hour!",
                #     "bonus": lambda xp: xp * 3,
                #     "duration": 1  # hour
                # },

            ]
        except Exception as e:
            print(f"Error in XPBonus.__init__: {e}")


async def setup(bot):
    await bot.add_cog(XPCore(bot))

