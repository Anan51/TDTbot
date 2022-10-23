import discord  # type: ignore # noqa: F401
from discord.ext import commands  # type: ignore
import asyncio
from .. import param  # roles
from ..helpers import find_role
from ..async_helpers import split_send
from ..version import usingV2
import logging
import re


logger = logging.getLogger('discord.' + __name__)


# below are unacceptable words and phrases
_bad_words = ['fag', 'faggot', 'nigger', "debug_testing_bad_word"]
_searches = [r'(?i)\bkill\byourself\b',
             r'\b(https:\/\/)?discord\.gg(\/\w+)\b',
             ]
_searches += [r'(?i)\b{:}\b'.format(i) for i in _bad_words]


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._log_channel = None
        self._init = False
        self._mentions = None
        self._coc_link = None

    async def _async_init(self):
        if self._init:
            return
        self.log_channel
        self.mentions
        self._init = True

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(5)
        await self._async_init()

    @property
    def mentions(self):
        if self._mentions is not None:
            self._mentions = [find_role(self.bot.tdt(), i).mention
                              for i in ["admin", "devoted"]]
        return self._mentions

    @property
    def log_channel(self):
        if self._log_channel is None:
            self._log_channel = self.bot.find_channel(param.rc('log_channel'))
        return self._log_channel

    async def fetch_coc_link(self):
        if self._coc_link:
            return self._coc_link
        channel = self.bot.find_channel(param.rc('manual_page'))
        msg = await channel.fetch_message(param.messages.coc)
        self._coc_link = msg.jump_url
        return self._coc_link

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
                msg = ["I have parsed this message as spam as against the CoC and deleted it:\n",
                       "```{:}```\n".format(message.content),
                       "From: {:} ({:}, {:})\n".format(message.author.mention, message.author.name, message.author.id),
                       "In: {:} ({:})\n".format(message.channel.mention, message.channel.name),
                       self.mentions,
                       ]
                await split_send(self.log_channel, msg)
                msg = "I have parsed this message as spam as against the Code of Conduct (CoC) and deleted it.\n"
                msg += "Please read the CoC: " + await self.fetch_coc_link()
                await message.channel.send(msg, reference=message)
                await message.delete()
                return


if usingV2:
    async def setup(bot):
        cog = AutoMod(bot)
        await bot.add_cog(cog)
else:
    def setup(bot):
        bot.add_cog(AutoMod(bot))
