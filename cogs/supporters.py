import discord  # type: ignore # noqa: F401
from discord.ext import commands  # type: ignore
import os
import logging
import pytz
from typing import Union
from .. import param
from ..helpers import int_time, find_role, seconds_to_datetime
from ..async_helpers import admin_check, split_send
from ..version import usingV2


roles = param.roles
logger = logging.getLogger('discord.' + __name__)
supporters_fn = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
supporters_fn = os.path.join(supporters_fn, 'config', 'supporters.dbm')
_min_support_role = roles.community
_user_t = Union[discord.Member, discord.User]
_training_key = '<debug_training>'
_nmax = 20


class Supporters(commands.Cog):
    """Store and list supporters"""
    def __init__(self, bot):
        self.bot = bot
        self.data = param.IntPermaDict(supporters_fn)
        self._trainings = []
        self._bounty_board = None

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
        role = find_role(ctx.guild, _min_support_role)
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
        """<member>: retrieves supporter info for member."""
        try:
            await ctx.send(self._str(member))
        except KeyError:
            await ctx.send('No member "{}" found in supporters.'.format(member))

    @commands.command(aliases=['remove_supporter'])
    async def delete_supporter(self, ctx, member: _user_t):
        """<member>: removes member from supporter list."""
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
                f = lambda x: self.data[x][0]  # noqa: E731
            elif sort_by == 'id':
                f = lambda x: x  # noqa: E731
            elif sort_by == 'name':
                f = lambda x: members[x].display_name  # noqa: E731
            elif sort_by == 'alias':
                def f(x):
                    out = self.data[x][1] + '~~~'
                    return out + getattr(members[x], 'display_name', getattr(members[x], 'name', ''))
            else:
                await ctx.send("Unknown sort option.")
            keys = sorted(keys, key=f, reverse=reverse)
        lines = [self._str(members[key], key) for key in keys]
        if lines:
            await split_send(ctx, lines)
        else:
            await ctx.send("Empty supporter data.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for supporters asking for training"""
        supporter = False
        for role in message.author.roles:
            if role.id == param.roles.supporter:
                supporter = True
                break
        if not supporter:
            return
        if _training_key not in message.content.lower():
            return
        self._trainings.append(message.id)
        if len(self._trainings) > _nmax:
            self._trainings.pop(0)
        await message.add_reaction('⚔️')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Listen for reactions to training messages"""
        if payload.message_id not in self._trainings:
            return
        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if payload.emoji.name != '⚔️':
            return
        msg = 'Training request by {} here: {}.'.format(message.author.mention, message.jump_url)
        msg += '\nPlease help if you can.'
        if not self._bounty_board:
            self._bounty_board = self.bot.get_channel(param.channels.bounty_board)
        await self._bounty_board.send(msg)
        await message.add_reaction('✅')


if usingV2:
    async def setup(bot):
        cog = Supporters(bot)
        await bot.add_cog(cog)
else:
    def setup(bot):
        bot.add_cog(Supporters(bot))
