import discord
from discord.ext import commands
import logging
import re
from ..helpers import *
from .. import param


logger = logging.getLogger('discord.' + __name__)


_regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
_filetypes = dict()


def valid_url(url):
    return re.match(_regex, url) is not None


def parse_message(message):
    out = dict()
    out['urls'] = [i for i in message.content.split(' ') if valid_url(i)]
    out['attachments'] = [[i] + parse_filetype(i.filename) for i in message.attachments]
    out['content'] = message.content
    _type = []
    if out['urls']:
        _type.append('url')
    _type += [i[-1] for i in out['attachments']]
    if not _type:
        _type = ['normal']
    _type = sorted(list(set(_type)))
    out['type'] = _type
    return out


class Testing(commands.Cog):
    """Cog designed for debugging the bot"""
    def __init__(self, bot):
        self.bot = bot

    async def _can_run(self, ctx):
        """Don't allow everyone to access this cog"""
        if ctx.channel != self.bot.find_channel(param.rc('log_channel')):
            return False
        a = ctx.author
        if a.roles[0].name in ['Admin', 'Devoted']:
            return True
        if await self.bot.is_owner(a):
            return True
        if ctx.guild.owner == a:
            return True
        return False

    async def cog_check(self, ctx):
        return await self._can_run(ctx)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        # await message.channel.send(str(message))
        data = parse_message(message)
        for key in sorted(data.keys()):
            if data[key]:
                await message.channel.send(key + ":\n```" + str(data[key]) + '```')


def setup(bot):
    bot.add_cog(Testing(bot))
