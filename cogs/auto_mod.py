import discord  # type: ignore # noqa: F401
from discord.ext import commands  # type: ignore
import asyncio
from .. import param  # roles
# from ..helpers import find_channel, find_role
# from ..async_helpers import admin_check
import logging
import re


logger = logging.getLogger('discord.' + __name__)


# below are unacceptable words and phrases
_bad_words = ['fag', 'faggot', 'nigger', "debug_testing_bad_word"]
_searches = [r'(?i)\bkill\byourself\b'
             ]
_searches += [r'(?i)\b{:}\b'.format(i) for i in _bad_words]


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._log_channel = None
        self._init = False

    async def _async_init(self):
        if self._init:
            return
        self.log_channel
        self._init = True

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(5)
        await self._async_init()

    @property
    def log_channel(self):
        if self._log_channel is None:
            self._log_channel = self.bot.find_channel(param.rc('log_channel'))
        return self._log_channel

    @commands.Cog.listener()
    async def on_message(self, message):
        """Parse messages to see if we should roast even without a command"""
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
        for search in _searches:
            if re.search(search, message.content):
                msg = "I have parsed this message as spam as against the CoC and deleted it:\n"
                msg += "```{:}```\n".format(message.content)
                msg += "From: {:} ({:}, {:})\n".format(message.author.mention, message.author.name, message.author.id)
                msg += "In: {:} ({:})".format(message.channel.mention, message.channel.name)
                await self.log_channel.send(msg)
                msg = "I have parsed this message as spam as against the CoC and deleted it."
                await message.channel.send(msg, reference=message)
                await message.delete()
                return


def setup(bot):
    bot.add_cog(AutoMod(bot))
