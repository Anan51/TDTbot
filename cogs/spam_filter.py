import asyncio
import datetime
import discord
from discord.ext import commands
from .. import param, roles
from ..helpers import *
from ..async_helpers import admin_check
import logging
import re


logger = logging.getLogger('discord.' + __name__)
spam_msg = "I have parsed this message as spam. Please don't spam. This is a bot and I don't like spam. ({:})"


class SpamFilter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._init = False
        self._tdt = None
        self._com = None
        self._admin = None

    async def _async_init(self):
        if self._init:
            return
        _ = self.tdt
        _ = self.com
        _ = self.admin
        self._init = True

    @property
    def tdt(self):
        if self._tdt is None:
            self._tdt = self.bot.tdt()
        return self._tdt

    @property
    def com(self):
        if self._com is None:
            self._com = find_role(self.tdt, roles.community)
        return self._com

    @property
    def admin(self):
        if self._admin is None:
            self._admin = find_role(self.tdt, roles.admin)
        return self._admin

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(5)
        await self._async_init()

    async def reply_to_spam(self, message):
        """Reply to a spam post"""
        await message.channel.send(spam_msg.format(self.admin.mention), reference=message)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Parse messages for spam posts"""
        # ignore all messages from our bot
        if message.author == self.bot.user:
            return
        if not self._init:
            await self._async_init()
        if not isinstance(message.author, discord.Member):
            message.author = await self.bot.get_or_fetch_user(message.author.id)
        if not re.search(r'https://dis[discorde]{4}(.gift|[.]?com)+/[\w]+( |$)', message.content):
            return
        low_role = False
        if isinstance(message.author, discord.Member):
            if message.author.top_role <= self.com:
                low_role = True
        print('=> SPAM DETECTED:', message)
        return
        if low_role:
            try:
                await message.delete()
            except discord.Forbidden:
                if not isinstance(message.channel, discord.DMChannel):
                    await self.reply_to_spam(message)
        else:
            await self.reply_to_spam(message)


def setup(bot):
    bot.add_cog(SpamFilter(bot))

