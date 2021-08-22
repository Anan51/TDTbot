import discord
from discord.ext import commands
import datetime
import pytz
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
_tmax = datetime.timedelta(days=90)
_role2emoji = {'pc': 'steam'}
_tz = pytz.timezone(param.rc('timezone'))

# todo: auto react(drop or update?), CoC rxn for role/multi-lfgs


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

    def _clear_old(self, key):
        old = (datetime.datetime.utcnow() - _tmax).timestamp()
        if key in self:
            pops = [i for i in self[key] if i[1] < old]
            for p in pops:
                self[key].pop(p)

    def update_pings(self, msg, roles):
        user_id = msg.author.id
        self._clear_old(user_id)
        entry = [msg.id, msg.created_at.timestamp()] + roles
        if user_id in self:
            self[user_id].append(entry)
        else:
            self[user_id] = [entry]

    def _fmt_row(self, row):
        msg = row[0]
        # assign UTC timezone
        dt = pytz.utc.localize(datetime.datetime.fromtimestamp(row[1]))
        # convert to server timezone
        dt = dt.astimezone(_tz)
        roles = ' '.join([':{}:'.format(_role2emoji.get(i, i)) for i in row[2:]])
        return roles + ' {}; message ID: {}'.format(dt, msg)

    def member_list(self, mid):
        out = []
        if mid in self:
            out = [self._fmt_row(i) for i in self[mid]]
        return out

    def member_summary(self, mid):
        data = self[mid]
        tot = len(data)
        roles = dict()
        for d in data:
            for role in d[2:]:
                if role in roles:
                    roles[role] += 1
                else:
                    roles[role] = 1
        return tot, roles


class LFG(commands.Cog):
    channels = [560270058224615425, 878403478987366490, 878403991195766844]

    def __init__(self, bot, debug=False):
        self.bot = bot
        self._last_member = None
        self._kicks = []
        self.data = _ActivityFile()
        self._init = False
        self._init_finished = False
        self._debug = debug
        self._cached_search = None

    def _get_emoji(self, role, guild):
        emoji = _role2emoji.get(role, role)
        try:
            return [e for e in guild.emojis if e.name == emoji][0]
        except IndexError:
            return ''

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
        if message.channel.id in self.channels:
            return
        roles_tagged = []
        for role in message.role_mentions:
            if role.name.endswith(' D2'):
                name = role.name[:-3].lower()
                # role -> emoji
                emoji = _role2emoji.get(name, name)
                emoji = [e for e in message.guild.emojis if e.name == emoji][0]
                await message.add_reaction(emoji)
                roles_tagged.append(name)
        if roles_tagged:
            self.data.update_pings(message, roles_tagged)

    @commands.command()
    @commands.check(admin_check)
    async def ping_data(self, ctx, member: discord.User = None):
        if member is None:
            member = ctx.author
        await split_send(ctx, self.data.member_list(member.id))

    @commands.command()
    @commands.check(admin_check)
    async def ping_summary(self, ctx, member: discord.User = None):
        if member is None:
            member = ctx.author
        tot, data = self.data.member_summary(member.id)
        out = 'Total: {}; '.format(tot)
        out += ', '.join(['{} :{}:'.format(value, self._get_emoji(role, ctx.guild)) for
                          role, value in data.items()])
        await ctx.send(out)


def setup(bot):
    """This is required to add this cog to a bot as an extension"""
    bot.add_cog(LFG(bot))
