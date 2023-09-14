import discord
from discord.ext import commands

class CreateEmbed(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.get_cog("Database")

    async def create_embed(self, title=None, description=None, color=None,
                           footer_text=None, footer_icon=None,
                           image_url=None, thumbnail_url=None,
                           author_name=None, author_icon_url=None, author_url=None,
                           fields=None):
        """
        Create a Discord embed with the given parameters.

        :param title: Title of the embed.
        :param description: Description of the embed.
        :param color: Color of the embed.
        :param footer_text: Text for the footer.
        :param footer_icon: Icon URL for the footer.
        :param image_url: URL of the image to be displayed.
        :param thumbnail_url: URL of the thumbnail to be displayed.
        :param author_name: Name of the author.
        :param author_icon_url: Icon URL for the author.
        :param author_url: URL for the author section.
        :param fields: List of fields. Each field is a tuple (name, value, inline).
        :return: A discord.Embed object.
        """
        print(f"Setting title in create_embed: {title}")  # Debugging
        print(f"Setting description in create_embed: {description}")  # Debugging

        embed = discord.Embed(title=title, description=description, color=color)

        if footer_text:
            embed.set_footer(text=footer_text, icon_url=footer_icon)
        
        if image_url:
            embed.set_image(url=image_url)
        
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
        
        if author_name:
            embed.set_author(name=author_name, icon_url=author_icon_url, url=author_url)
        
        if fields:
            for field in fields:
                name, value, inline = field
                embed.add_field(name=name, value=value, inline=inline)

        # print(f"Embed title after setting in create_embed: {embed.title}")  # Debugging
        # print(f"Embed description after setting in create_embed: {embed.description}")  # Debugging
        return embed

async def setup(bot):
    await bot.add_cog(CreateEmbed(bot))
