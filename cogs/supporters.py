import os
import discord
from discord.ext import commands
import logging
import pytz
from typing import Union
from .. import param, roles
from ..helpers import *
from ..async_helpers import admin_check, split_send


logger = logging.getLogger('discord.' + __name__)
supporters_fn = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
supporters_fn = os.path.join(supporters_fn, 'config', 'supporters.dbm')
_supporter_rank = roles.community
_user_t = Union[discord.Member, discord.User]


class Supporters(commands.Cog):
    """Store and list supporters"""
    def __init__(self, bot):
        self.bot = bot
        self.data = param.IntPermaDict(supporters_fn)

    async def cog_check(self, ctx):
        """Don't allow everyone to access this cog"""
        return await admin_check(ctx)

    @commands.command()
    async def add_supporter(self, ctx, member: _user_t, *args):
        """<member> <supporter name (optional)>: adds member to supporter list."""
        alias = ' '.join([str(i) for i in args])
        if member.id in self.data:
            msg = 'Member "{}" already in supporters.'.format(member)
            if alias:
                if not self.data[member.id][1]:
                    msg += '\nAdding supporter info "{}".'.format(alias)
                else:
                    msg += '\nModifying supporter info from "{}" to "{}".'
                    msg.format(self.data[member.id][1], alias)
            await ctx.send(msg)

        now = int_time()
        self.data[member.id] = [now, alias]
        reason = "User is a paid supporter"
        role = find_role(ctx.guild, _supporter_rank)
        if not isinstance(member, discord.Member):
            tmp = ctx.guild.get_member(member.id)
            member = tmp if tmp else member
        try:
            if member.top_role < role:
                await member.add_roles(role, reason=reason)
                recruit = find_role(ctx.guild, roles.recruit)
                if recruit in member.roles:
                    await member.remove_roles(recruit)
        except (AttributeError, discord.Forbidden):
            msg = 'Unable to promote {}, you must do so manually.'
            await ctx.send(msg.format(member))
            return
        await ctx.message.add_reaction('👍')

    def _str(self, member, mid):
        if not isinstance(member, int) and member is not None:
            enroll, alias = self.data[member.id]
            msg = str(member)
        else:
            enroll, alias = self.data[mid]
            msg = 'id: ' + str(mid)
        tz = pytz.timezone(param.rc('timezone'))
        enroll = seconds_to_datetime(enroll).astimezone(tz).strftime("%c")

        if alias:
            msg += ' (' + alias + ')'
        msg += ' Enrolled at: ' + enroll
        return msg

    @commands.command()
    async def retrieve_supporter(self, ctx, member: _user_t):
        try:
            await ctx.send(self._str(member))
        except KeyError:
            await ctx.send('No member "{}" found in supporters.'.format(member))

    @commands.command(aliases=['remove_supporter'])
    async def delete_supporter(self, ctx, member: _user_t):
        self.data.delete(member.id)
        try:
            msg = "Removed {}. Role changes must be done manually."
            await ctx.send(msg.format(member))
        except KeyError:
            await ctx.send('No member "{}" found in supporters.'.format(member))

    @commands.command()
    async def list_supporters(self, ctx, sort_by='alias'):
        """<optional sort key>: lists all supporters.keys
        sorting keys: alias      - supporter username/alias
                      date       - enrollment date and time
                      id         - user id number
                      name       - user name
                      <prefix>_r - reverse order (e.g. id_r)"""
        keys = self.data.keys()
        members = {key: await self.bot.get_or_fetch_user(key, ctx, fallback=True)
                   for key in keys if key}
        if sort_by is not None:
            reverse = False
            if sort_by.endswith('_r'):
                reverse = True
                sort_by = sort_by[:-2]
            if sort_by in ['date', 'datetime']:
                f = lambda x: self.data[x][0]
            elif sort_by == 'id':
                f = lambda x: x
            elif sort_by == 'name':
                f = lambda x: members[x].display_name
            elif sort_by == 'alias':
                f = lambda x: self.data[x][1] + '~~~' + \
                              getattr(members[x], 'display_name',
                                      getattr(members[x], 'name', ''))
            else:
                await ctx.send("Unknown sort option.")
            keys = sorted(keys, key=f, reverse=reverse)
        lines = [self._str(members[key], key) for key in keys]
        if lines:
            await split_send(ctx, lines)
        else:
            await ctx.send("Empty supporter data.")


def setup(bot):
    bot.add_cog(Supporters(bot))
