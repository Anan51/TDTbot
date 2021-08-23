import os
import discord
from discord.ext import commands
import logging
import pytz
import shelve
from .. import param
from ..helpers import *
from ..async_helpers import admin_check, split_send


logger = logging.getLogger('discord.' + __name__)
_dbm = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
_dbm = os.path.join(_dbm, 'config', 'supporters.dbm')


class Supporters(commands.Cog):
    """Store and list supporters"""
    def __init__(self, bot):
        self.bot = bot
        self.data = shelve.open(_dbm)

    async def cog_check(self, ctx):
        """Don't allow everyone to access this cog"""
        return await admin_check(ctx)

    @commands.command()
    async def add_supporter(self, ctx, member: discord.User, *args):
        """<member> <supporter name (optional)>: adds member to supporter list."""
        if member.id in self.data:
            await ctx.send('Member "{}" already in supporters.'.format(member))
            return
        alias = ' '.join([str(i) for i in args])
        now = int_time()
        self.data[member.id] = [now, alias]
        await ctx.message.add_reaction('👍')

    def _str(self, member):
        enroll, alias = self.data[member.id]
        tz = pytz.timezone(param.rc('timezone'))
        enroll = seconds_to_datetime(enroll).astimezone(tz).strftime("%c")
        msg = str(member)
        if alias:
            msg += ' (' + alias + ')'
        msg += ' Enrolled at: ' + enroll
        return msg

    @commands.command()
    async def retrieve_supporter(self, ctx, member: discord.User):
        try:
            await ctx.send(self._str(member))
        except KeyError:
            await ctx.send('No member "{}" found in supporters.'.format(member))

    @commands.command()
    async def list_supporters(self, ctx, sort_by=None):
        """<optional sort key>: lists all supporters.keys
        sorting keys: date - enrollment date and time
                      id   - user id number
                      name - user name"""
        keys = self.data.keys()
        members = {key: await self.bot.get_or_fetch_user(key, ctx) for key in keys}
        if sort_by is not None:
            if sort_by in ['date', 'datetime']:
                f = lambda x: self.data[x][0]
            elif sort_by == 'id':
                f = lambda x: x
            elif sort_by == 'name':
                f = lambda x: members[x].display_name
            elif sort_by == 'alias':
                f = lambda x: self.data[x][0] + '~~~' + members[x].display_name
            keys = sorted(keys, key=f)
        lines = [self._str(key) for key in keys]
        await split_send(ctx, lines)


def setup(bot):
    bot.add_cog(Supporters(bot))
