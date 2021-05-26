import discord
from discord.ext import commands
from ..helpers import *
import logging


logger = logging.getLogger('discord.' + __name__)

_channel = 562412283268169739
_emojis = ['👍', '💩']


class Lenny(commands.Cog):
    """Cog for trick or treat game"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Parse messages for new event post"""
        # ignore non-lenny channels
        if message.channel.id != _channel:
            return
        # ignore commands
        try:
            if message.content.startswith(self.bot.command_prefix):
                return
        except TypeError:
            for prefix in self.bot.command_prefix:
                if message.content.startswith(prefix):
                    return
        # ignore messages from this bot
        if message.author == self.bot.user:
            return
        data = parse_message(message)
        for i in data['type']:
            if i.startswith('image/') or i.startswith('url'):
                for e in _emojis:
                    await message.add_reaction(e)


def setup(bot):
    bot.add_cog(Lenny(bot))
