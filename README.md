# LittleRoomDev Bot

LittleRoomDev Bot (or LRD Bot) is a Discord bot tailored for the LRD Discord admins. It's built using Python and the discord.py library and utilizes SQLite for data storage.

## Features

- **FAQ System**: When an admin or a user replies with `FAQ #<number>`, the bot fetches the FAQ content from the database and replies to the user mentioning them with the content.
  
- **Admin Controls**: Admins can easily manage various bot settings through the `/setup` slash command, which includes:
  - Adding or removing FAQs.
  - Setting roles with admin permissions for the bot.
  - Setting channels for specific functionalities, including the showcase channel.

- **Showcase Channel**: Users can showcase their work in the showcase channel, where the bot ensures that each user can only make one post per day. A forum (thread) is created under each post for discussions.

- **Welcome New Users**: When a new user joins the server, they receive a private message with the server rules. Additionally, on the rules page, buttons allow users to choose specific roles like "I have read the rules", "Patreon Announcements", etc.

## Installation

1. Clone this repository.
2. Install the required Python packages: `pip install -r requirements.txt`
3. Set up the SQLite database, ensuring the `database` directory exists.
4. Update the `.env` file with the necessary configurations, including your bot's token.
5. Build the Docker image: `docker build -t lrd_bot:latest .`
6. Run the Docker container: `docker run -v %cd%/database:/app/database lrd_bot:latest`

## Usage

Once the bot is running and has been invited to your server, you can use the slash commands. For instance, the `/setup` command provides an interactive way for admins to configure the bot. The bot's features like the FAQ system, Showcase Channel moderation, and welcoming new users are automated.

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## Discord

[Join our Discord server](https://discord.gg/CmrFZgZVEE)

## License

This project is licensed under the MIT License.
