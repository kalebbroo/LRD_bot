# LittleRoomDev Bot

LittleRoomDev Bot (LRD Bot) is a custom Discord bot tailored for the LRD Discord server. Powered by Python and the discord.py library, the bot also employs SQLite for data storage, ensuring a seamless user experience.

## Features

- **FAQ System**: 
  - A dynamic FAQ system that can be managed by admins.
  - A user or admin can invoke the FAQ command in a few ways. (`!FAQ`) while sending a message to a user or (`/FAQ`) as a slash command. It also takes a second arg to specify a specific FAQ. Activate it by its number (`!FAQ #<number>`), or (`/FAQ #<number>`)the bot retrieves the content from the database and provides a detailed response.
  
- **Admin Controls**: 
  - The `/setup` slash command offers a robust interface for admins to configure various bot functionalities, This must be completed before you can use the bot:
    - **Map Channel Names to Database**: Map all the channels that the bot will need to send messages to or use in some way. Examples include Welcome/rules, bot spam, admin, showcase, etc..
    - **Map Roles and Create Buttons**: Map to roles to buttons that will be displayed on the welcome/rules page. This will allow a user to click the button and gain/remove the role.
    - **Welcome Page Setup**: This will map a channel to the db and you will set the message for the user. Under this message all the role buttons you mapped will be created and posted. This post will refresh this message and buttons on bot restart just to make sure the buttons stay active. 
    - **Add FAQ**: Easily define and incorporate a new FAQ entry.
    - **Remove FAQ**: Swiftly delete any existing FAQ.

- **Showcase Channel**: 
  - A unique space for users to display their work.
  - The bot ensures that each user can only create one post per day to maintain a clutter-free environment.
  - Every showcase post spawns a dedicated thread for discussions, enabling constructive feedback and conversations.

- **Welcoming New Users**: 
  - Every new member receives a direct message detailing the server rules.
  - The rules page is equipped with interactive buttons, permitting users to select specific roles such as "I have read the rules", "Patreon Announcements", and more.
  - The welcome page also includes an interactive tutorial to guide new members through the server's features and how to use them. This interactive experience ensures new members get acquainted with the server quickly.

- **XP & Rank System**:
  - Users earn XP for their participation and activity in the server. There may also be special events that can give bonuses.
    - Ways to earn XP:
      1. Sending Messages:
        - Base XP: Random between 5-50.
        - Modifiers: Double XP Day Event (2x), Active User Reward Event (+20%).
        
      2. Adding Reactions:
        - Base XP: 1 XP per reaction.
        - Penalty: -100 XP for spamming reactions.
        - Modifiers: Emoji Madness Event Event (10x).

      3. Streaming in Voice Channels:
        - Base XP: 10 XP for starting a stream.
        - Extra: +5 XP every 10 minutes if at least 4 viewers.
        - Modifiers: Voice Chat Vibes Event (+50%).

      4. Using Slash Commands:
        - Base XP: random XP between 5-50.
        - Modifiers: Playing With Bots Event (+10%).

      5. Adding Showcase Posts:
        - Add a new showcase post that gets approved.
        - Users can upvote your post and you will gain random amount of XP. 

  - The bot automatically sends a **Level Up** card to users when they reach a new level.
  - Users can use the `/rank` command to view their rank card, which displays their current level, XP, and rank image. (#add images here when I have them.)

- **Mute System**: 
  - Admins can mute disruptive users, preventing them from speaking or sending messages.
  - The bot ensures that the "Muted" role permissions are applied to every channel, including those created after the bot starts.

- **Warning System**:
  - Admins can issue warnings to users for violations of server rules.
  - Accumulated warnings can lead to automatic penalties such as mutes or bans.
  - The bot keeps a log of all warnings to ensure consistent moderation.
  - You can display user warnings by using the `/view_warnings` slash command.

- **Listeners**: 
  - **Support Channel Listener**: When certain keywords are detected in messages outside the support channel, the bot gently redirects users to the correct channel.
  - **New Channel Listener**: When a new channel is created, the bot ensures the "Muted" role has its permissions set correctly for the new channel.

- **Database Storage**: 
  - The SQLite database stores various data, such as:
    - User information like number of posts, reactions, times nickname was changed, etc..
    - FAQs and their associated numbers.
    - Role Buttons and Channel mappings.
    - User posts in the showcase channel to enforce the one post per day rule and votes.
    - Moderation logs to keep track of user actions like mutes, bans, etc.

## Installation

1. Clone this repository.
2. Update the `.env` file with the necessary configurations, particularly your bot's token.
3. Run the provided install script.
  - windows_install.bat for Windows
  - linux_install.sh for Linux. (run it in terminal or make it exicutable)
4. Setup the bot using the `/setup` command. Use `/help` for details.
5. profit.

## Contributing

I appreciate contributions! If you have improvements or bug fixes, please submit a pull request.

## Discord

Wish to test out my bots? [Join my Dev Discord server](https://discord.gg/CmrFZgZVEE).

## License

This project is licensed under the MIT License.