# LittleRoomDev Bot

LittleRoomDev Bot (LRD Bot) is a custom Discord bot tailored for the LRD Discord server. Powered by Python and the discord.py library, the bot also employs SQLite for data storage, ensuring a seamless user experience.

## Features

- **FAQ System**: 
  - A dynamic FAQ system that can be managed by admins.
  - When a user or admin references an FAQ by its number (`FAQ #<number>`), the bot retrieves the content from the database and provides a detailed response.
  
- **Admin Controls**: 
  - The `/setup` slash command offers a robust interface for admins to configure various bot functionalities, such as:
    - **Add FAQ**: Easily define and incorporate a new FAQ entry.
    - **Remove FAQ**: Swiftly delete any existing FAQ.
    - **Set Role**: Integrate pre-defined roles with actual roles in the server.
    - **Set Channel**: Assign specific bot functionalities to designated channels.
    
- **Showcase Channel**: 
  - A unique space for users to display their work.
  - The bot ensures that each user can only create one post per day to maintain a clutter-free environment.
  - Every showcase post spawns a dedicated thread for discussions, enabling constructive feedback and conversations.

- **Welcoming New Users**: 
  - Every new member receives a direct message detailing the server rules.
  - The rules page is equipped with interactive buttons, permitting users to select specific roles such as "I have read the rules", "Patreon Announcements", and more.

- **Mute System**: 
  - Admins can mute disruptive users, preventing them from speaking or sending messages.
  - The bot ensures that the "Muted" role permissions are applied to every channel, including those created after the bot starts.

- **Listeners**: 
  - **Support Channel Listener**: When certain keywords are detected in messages outside the support channel, the bot gently redirects users to the correct channel.
  - **New Channel Listener**: When a new channel is created, the bot ensures the "Muted" role has its permissions set correctly for the new channel.

- **Database Storage**: 
  - The SQLite database stores various data, such as:
    - FAQs and their associated numbers.
    - Role mappings.
    - User posts in the showcase channel to enforce the one post per day rule.
    - Moderation logs to keep track of user actions like mutes, bans, etc.

## Installation

1. Clone this repository.
2. Install the required Python packages using: `pip install -r requirements.txt`
3. Ensure the `database` directory exists for SQLite storage.
4. Update the `.env` file with the necessary configurations, particularly your bot's token.
5. Build the Docker image with: `docker build -t lrd_bot:latest .`
6. Launch the Docker container using: `docker run -v %cd%/database:/app/database lrd_bot:latest`

## Usage

With the bot active and integrated into your server, you can harness the power of slash commands. For example, the `/setup` command grants admins an interactive interface to calibrate the bot. Automated features, such as the FAQ system, Showcase Channel moderation, and user welcome sequences, require no manual intervention.

## Contributing

We appreciate contributions! If you have improvements or bug fixes, please submit a pull request.

## Discord

Wish to discuss more? [Join our Discord server](https://discord.gg/CmrFZgZVEE).

## License

LRD Bot is licensed under the MIT License.

