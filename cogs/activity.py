import datetime
import discord
from discord.ext import commands
import logging
import pickle
import shelve
import os
from .. import param
from ..helpers import *
from ..async_helpers import *


logger = logging.getLogger('discord.' + __name__)
_limit = 5000
_epoch = datetime.datetime(2000, 1, 1)
_dbm = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
_dbm = os.path.join(_dbm, 'config', 'activity.dbm')


def _int_time(in_time=None, epoch=None):
    if in_time is None:
        in_time = datetime.datetime.utcnow()
    if epoch is None:
        epoch = _epoch
    return int((in_time - epoch).total_seconds())


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

    def update_activity(self, user_id, in_time=None):
        now = _int_time(in_time=in_time)
        user_id = str(int(user_id))
        if user_id in self:
            try:
                self[user_id] = max(now, self[user_id])
            except pickle.UnpicklingError:
                self[user_id] = now
        else:
            self[user_id] = now

    def inactive(self, dt=None, return_dict=False):
        if dt is None:
            dt = datetime.timedelta(days=7)
        dt = int(dt.total_seconds())
        now = _int_time()
        if return_dict:
            return {int(i): self.file.get(i, 0) for i in self.file
                    if now - self.file.get(i, 0) > dt}
        else:
            return [int(i) for i in self.file if now - self.file.get(i, 0) > dt]

    async def fetch_and_sort(self, guild, inactive=None, dt=None):
        if inactive is None:
            inactive = self.inactive(dt=dt, return_dict=True)
        inactive = sorted(inactive.items(), key=lambda x: x[1])
        out = []
        for i in inactive:
            member = guild.get_member(i[0])
            if member is None:
                try:
                    member = await guild.fetch_member(i[0])
                except discord.errors.NotFound:
                    continue
            if member is not None:
                out.append([member, _epoch + datetime.timedelta(seconds=i[1])])
        return out


class Activity(commands.Cog):
    def __init__(self, bot, debug=False):
        self.bot = bot
        self._last_member = None
        self._kicks = []
        self.data = _ActivityFile()
        self._init = False
        self._init_finished = False
        self._debug = debug
        self._cached_search = None

    async def cog_check(self, ctx):
        """Don't allow everyone to access this cog"""
        return await admin_check(ctx)

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(5)
        await self._async_init()

    async def _async_init(self):
        if self._init:
            return
        self._init = True
        data = await self._hist_search(limit=100, use_ids=True, save=True)
        for i in data:
            self.data.update_activity(i, data[i])
        data = await self._hist_search(limit=_limit, use_ids=True, save=True)
        for i in data:
            self.data.update_activity(i, data[i])
        self._init_finished = True

    async def _hist_search(self, guild=None, members=None, limit=1000, use_ids=False,
                           ctx=None, save=None):
        if guild is None:
            if ctx is None:
                guild = [g for g in self.bot.guilds if g.name == "The Dream Team"][0]
            else:
                guild = ctx.guild
        if members is None:
            members = guild.members
        data = dict()
        # get all channels with a history attribute
        channels = [i for i in guild.channels if hasattr(i, "history")]
        oldest = datetime.datetime.now()  # store the oldest time parsed
        old_af = _epoch  # just some really old date
        for channel in channels:
            try:
                # loop through messages in history (limit 1000 messages per channel)
                async for msg in channel.history(limit=limit):
                    # update oldest
                    oldest = min(oldest, msg.created_at)
                    # add/update data for message author
                    if msg.author in members:
                        key = msg.author
                        if use_ids:
                            key = key.id
                        try:
                            # use the most recent date
                            data[key] = max(data[key], msg.created_at)
                        except KeyError:
                            data[key] = msg.created_at
            except discord.Forbidden:
                # We do not have permission to read this channel's history
                logger.printv("Cannot read channel {0}.".format(channel))
        # make sure we have data for each member
        for member in members:
            key = member
            if use_ids:
                key = key.id
            if key not in data:
                # use join date if it's more recent than oldest
                if member.joined_at > oldest:
                    data[key] = member.joined_at
                else:
                    data[key] = old_af
                    print('old af: {}'.format(member))
        if save is None and self._cached_search is None:
            save = True
        if save:
            self._cached_search = data.copy()
            self._cached_search['use_ids'] = use_ids
        return data

    @commands.command()
    async def inactivity(self, ctx, role: discord.Role = None, dt: int = None):
        """<role (optional)> shows how long members have been inactive for."""
        await ctx.send("Hold on while I parse the server history.")
        await self._async_init()
        if dt is None:
            dt = datetime.timedelta(seconds=-1)
        else:
            dt = datetime.timedelta(days=dt)
        items = await self.data.fetch_and_sort(ctx.guild, dt=dt)
        if role in ['none', 'None']:
            role = None
        if role is not None:
            items = [i for i in items if role in i[0].roles]
        msg = ['{0.display_name} {1}'.format(i[0], i[1].date().isoformat())
               for i in items]
        await split_send(ctx, msg, style='```')

    @commands.command()
    async def purge(self, ctx, role: discord.Role = None):
        """<role (optional)> shows members that have been inactive for over a week."""
        await ctx.send("Hold on while I parse the server history.")
        await self._async_init()
        recruit = find_role(ctx.guild, "Recruit")
        items = await self.data.fetch_and_sort(ctx.guild)
        if role is not None:
            items = [i for i in items if role in i[0].roles]

        lowers = []
        output = []

        for i in items:
            if i[0].top_role == recruit:
                output.append(await self._demote(*i, debug=True))
            elif i[0].top_role <= recruit:
                if i[0].top_role.name not in ['Lone Wolf'] and not i[0].bot:
                    lowers.append(i)
        await split_send(ctx, output)

        for i in lowers:
            await self._prompt_kick(*i)

        return

    @commands.command()
    async def purge2(self, ctx, role: discord.Role = None):
        """Depreciated name for what is now purge"""
        await ctx.send("This command is now depreciated. I will run tdt$purge instead.")
        return await self.purge(ctx, role=role)

    async def _demote(self, m, dt, debug=None):
        if debug is None:
            debug = self._debug
        roles = [r for r in m.roles if r.name not in ['@everyone', 'Nitro Booster']]
        if not debug:
            await m.remove_roles(*roles, reason='Inactivity')
        date = dt.date().isoformat()
        return '{0.display_name} demoted (last active {1})'.format(m, date)

    async def _prompt_kick(self, m, dt, channel=None):
        if channel is None:
            channel = self.bot.find_channel(param.rc('log_channel'))
        date = dt.date().isoformat()
        msg = 'Should I kick {0.display_name} (#{0.discriminator}), last active {1}?'
        msg = await channel.send(msg.format(m, date))
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')
        self._kicks.append([msg, m])

    @commands.Cog.listener()
    async def on_message(self, message):
        self.data.update_activity(message.author.id)
        if not self._init:
            await self._async_init()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Parse reactions"""
        self.data.update_activity(payload.user_id)
        # if reaction is to a kick quarry
        ids = [k[0].id for k in self._kicks]
        if payload.message_id in ids:
            emoji = str(payload.emoji)
            if emoji in ['✅', '❌']:
                guild = await self.bot.fetch_guild(payload.guild_id)
                if await admin_check(author=payload.member, guild=guild):
                    if emoji == '✅':
                        index = ids.index(payload.message_id)
                        msg, member = self._kicks.pop(index)
                        if not self._debug:
                            await member.kick(reason='Inactivity')
                        await msg.add_reaction('🔨')
                        return
                    if emoji == '❌':
                        index = ids.index(payload.message_id)
                        msg, member = self._kicks.pop(index)
                        await msg.add_reaction('👌')
                        return

    @commands.command()
    async def activity_init_status(self, ctx):
        await ctx.send('init = {0._init}, init_finished = {0._init_finished}.'.format(self))

    @commands.command()
    async def parse_cached(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        name = member.display_name
        if self._cached_search.get('use_ids'):
            member = member.id
        value = self._cached_search[member]
        print(member, value)
        msg = ' '.join([str(i) for i in [name, value]])
        await ctx.send(msg)

    @commands.command()
    async def parse_data(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        name = member.display_name
        value = self.data[member.id]
        date = _epoch + datetime.timedelta(seconds=value)
        msg = ' '.join([str(i) for i in [name, value, date]])
        await ctx.send(msg)


def setup(bot):
    """This is required to add this cog to a bot as an extension"""
    bot.add_cog(Activity(bot))
