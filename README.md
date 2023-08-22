# LittleRoomDev Bot

LittleRoomDev Bot (or LRD Bot) is a Discord bot tailored for the LRD Discord admins. It's built using Python and the discord.py library and utilizes SQLite for data storage.

## Features

- **FAQ System**: When an admin or a user replies with FAQ #<number>, the bot fetches the FAQ content from the database and replies to the user mentioning them with the content.
- **Admin Controls**: Admins can easily manage FAQs, set roles with admin permissions for the bot, and set channels for specific functionalities using various commands.
- **Showcase Channel**: Users can showcase their work in the showcase channel, where the bot ensures that each user can only make one post per day. A forum (thread) is created under each post for discussions.

## Installation

1. Clone this repository.
2. Install the required Python packages: `pip install -r requirements.txt`
3. Set up the SQLite database, ensuring the `database` directory exists.
4. Update the `.env` file with the necessary configurations, including your bot's token.
5. Build the Docker image: `docker build -t lrd_bot:latest .`
6. Run the Docker container: `docker run -v %cd%/database:/app/database lrd_bot:latest`

## Usage

Once the bot is running and has been invited to your server, you can use the following commands:

- `!addFAQ <number> <content>`: Adds a FAQ to the database.
- `!removeFAQ <number>`: Removes a FAQ from the database.
- `!setRole <role_name>`: Sets roles which have admin permissions for the bot.
- `!setChannel <channel_type> <channel_id>`: Sets channels for specific functionalities.

(Note: The above are just a few examples. There are more commands provided by the bot for various functionalities.)

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## Discord

[Join our Discord server](https://discord.gg/CmrFZgZVEE)

## License

This project is licensed under the MIT License.

