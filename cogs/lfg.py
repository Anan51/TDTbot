import discord
from discord.ext import commands
import pickle
import shelve
import logging
import os
from .. import param
from ..helpers import *
from ..async_helpers import *


logger = logging.getLogger('discord.' + __name__)
_dbm = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
_dbm = os.path.join(_dbm, 'config', 'lfg.dbm')


class _ActivityFile:
    def __init__(self, fn=_dbm):
        self.fn = fn
        self.file = shelve.open(fn)

    def __del__(self):
        self.file.sync()
        self.file.close()

    def __getitem__(self, key):
        return self.file[str(key)]

    def __setitem__(self, key, value):
        self.file[str(key)] = value

    def get(self, key, default):
        return self.file.get(str(key), default)

    def __contains__(self, item):
        return str(item) in self.file

    def keys(self):
        return list(self.file.keys())

    def items(self):
        return self.file.items()


class LFG(commands.Cog):
    def __init__(self, bot, debug=False):
        self.bot = bot
        self._last_member = None
        self._kicks = []
        self.data = _ActivityFile()
        self._init = False
        self._init_finished = False
        self._debug = debug
        self._cached_search = None

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(5)
        await self._async_init()

    async def _async_init(self):
        if self._init:
            return
        self._init = True

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Parse reactions"""
        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        """Parse messages for new lfg post"""
        # if not lfg channel
        if message.channel.id != 560270058224615425:
            return
        role_tagged = False
        for role in message.role_mentions:
            if role.name.endswith(' D2'):
                name = role.name[:-3].lower()
                # role -> emoji
                emoji = {'pc': 'steam'}.get(name, name)
                emoji = [e for e in message.guild.emojis if e.name == emoji][0]
                await message.add_reaction(emoji)
                role_tagged = True


def setup(bot):
    """This is required to add this cog to a bot as an extension"""
    bot.add_cog(LFG(bot))
