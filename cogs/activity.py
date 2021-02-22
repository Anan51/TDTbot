import datetime
import discord
from discord.ext import commands
import logging
import shelve
import os
from .. import param
from ..helpers import *
from ..async_helpers import *


logger = logging.getLogger('discord.' + __name__)
_epoch = datetime.datetime(2000, 1, 1)
_dbm = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
_dbm = os.path.join(_dbm, 'config', 'activity.dbm')


def _int_time(in_time=None, epoch=None):
    if in_time is None:
        in_time = datetime.datetime.utcnow()
    if epoch is None:
        epoch = _epoch
    return int(in_time - epoch)


class _ActivityFile:
    def __init__(self, fn=_dbm):
        self.fn = fn
        self.file = shelve.open(fn)

    def __del__(self):
        self.file.sync()
        self.file.close()

    def __getitem__(self, key):
        return self.file[key]

    def __setitem__(self, key, value):
        self.file[key] = value

    @property
    def get(self):
        return self.file.get

    def __contains__(self, item):
        return item in self.file

    def keys(self):
        return list(self.file.keys())

    def update_activity(self, user_id, in_time=None):
        now = _int_time(in_time=in_time)
        user_id = int(user_id)
        self[user_id] = max(now, self.file.get(user_id, 0))

    def inactive(self, dt=None, return_dict=False):
        if dt is None:
            dt = datetime.timedelta(days=7)
        dt = int(dt)
        now = _int_time()
        if return_dict:
            return {i: now - self.file.get(i, 0) for i in self.file
                    if now - self.file.get(i, 0) > dt}
        else:
            return [i for i in self.file if now - self.file.get(i, 0) > dt]


class Activity(commands.Cog):
    def __init__(self, bot, debug=False):
        self.bot = bot
        self._last_member = None
        self._kicks = []
        self.data = _ActivityFile()
        self._init = False
        self._debug = debug

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
        data = await self._hist_search(limit=5000, use_ids=True)
        for i in data:
            self.data.update_activity(i, data[i])

    async def _hist_search(self, guild=None, members=None, limit=1000, use_ids=False,
                           ctx=None):
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
        old_af = datetime.datetime(1, 1, 1)  # just some really old date
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
                # await ctx.send("Cannot read channel {0}.".format(channel))
                pass
        # make sure we have data for each member
        for member in members:
            if member not in data:
                key = member
                if use_ids:
                    key = key.id
                # use join date if it's more recent than oldest
                if member.joined_at > oldest:
                    data[key] = member.joined_at
                else:
                    data[key] = old_af
        return data

    @commands.command()
    async def old_inactivity(self, ctx, role: discord.Role = None):
        """<role (optional)> shows how long members have been inactive for."""
        await ctx.send("Hold on while I parse the server history.")
        if role is None:
            members = ctx.guild.members
        else:
            members = role.members
        data = dict()
        # get all channels with a history attribute
        channels = [i for i in ctx.guild.channels if hasattr(i, "history")]
        oldest = datetime.datetime.now()  # store the oldest time parsed
        old_af = datetime.datetime(1, 1, 1)  # just some really old date
        for channel in channels:
            try:
                # loop through messages in history (limit 1000 messages per channel)
                async for msg in channel.history(limit=1000):
                    # update oldest
                    oldest = min(oldest, msg.created_at)
                    # add/update data for message author
                    if msg.author in members:
                        try:
                            # use the most recent date
                            data[msg.author] = max(data[msg.author], msg.created_at)
                        except KeyError:
                            data[msg.author] = msg.created_at
            except discord.Forbidden:
                # We do not have permission to read this channel's history
                # await ctx.send("Cannot read channel {0}.".format(channel))
                pass
        # make sure we have data for each member
        for member in members:
            if member not in data:
                # use join date if it's more recent than oldest
                if member.joined_at > oldest:
                    data[member] = member.joined_at
                else:
                    data[member] = old_af
        # sort members with most inactive 1st
        items = sorted(data.items(), key=lambda x: x[1])
        msg = ['{0.display_name} {1}'.format(i[0], i[1].date().isoformat())
               for i in items]
        await split_send(ctx, msg, style='```')

    @commands.command()
    async def old_purge(self, ctx, role: discord.Role = None):
        """<role (optional)> shows members that have been inactive for over a week."""
        await ctx.send("Hold on while I parse the server history.")
        if role is None:
            members = ctx.guild.members
        else:
            members = role.members
        data = dict()
        # get all channels with a history attribute
        channels = [i for i in ctx.guild.channels if hasattr(i, "history")]
        oldest = datetime.datetime.now()  # store the oldest time parsed
        old_af = datetime.datetime(1, 1, 1)  # just some really old date
        for channel in channels:
            try:
                # loop through messages in history (limit 1000 messages per channel)
                async for msg in channel.history(limit=1000):
                    # update oldest
                    oldest = min(oldest, msg.created_at)
                    # add/update data for message author
                    if msg.author in members:
                        try:
                            # use the most recent date
                            data[msg.author] = max(data[msg.author], msg.created_at)
                        except KeyError:
                            data[msg.author] = msg.created_at
            except discord.Forbidden:
                # We do not have permission to read this channel's history
                # await ctx.send("Cannot read channel {0}.".format(channel))
                pass
        # make sure we have data for each member
        for member in members:
            if member not in data:
                # use join date if it's more recent than oldest
                if member.joined_at > oldest:
                    data[member] = member.joined_at
                else:
                    data[member] = old_af
        # sort members with most inactive 1st
        last_week = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        items = [i for i in sorted(data.items(), key=lambda x: x[1]) if i[1] < last_week]

        msg = ['{0.display_name} {1}'.format(i[0], i[1].date().isoformat())
               for i in items]
        await split_send(ctx, sorted(msg, key=str.lower), style='```')

    @commands.command()
    async def old_purge2(self, ctx):
        """Demote (kick) recruits (rankless) who've been inactive for a
        week."""
        await ctx.send("Hold on while I parse the server history.")
        recruit = find_role(ctx.guild, "Recruit")
        members = []
        async for member in ctx.guild.fetch_members(limit=2000):
            if not member.bot:
                if member.top_role <= recruit:
                    members.append(member)
        data = dict()
        # get all channels with a history attribute
        channels = [i for i in ctx.guild.channels if hasattr(i, "history")]
        oldest = datetime.datetime.now()  # store the oldest time parsed
        old_af = datetime.datetime(1, 1, 1)  # just some really old date
        for channel in channels:
            try:
                # loop through messages in history (limit 1000 messages per channel)
                async for msg in channel.history(limit=1000):
                    # update oldest
                    oldest = min(oldest, msg.created_at)
                    # add/update data for message author
                    if msg.author in members:
                        try:
                            # use the most recent date
                            data[msg.author] = max(data[msg.author], msg.created_at)
                        except KeyError:
                            data[msg.author] = msg.created_at
            except discord.Forbidden:
                # We do not have permission to read this channel's history
                # await ctx.send("Cannot read channel {0}.".format(channel))
                pass
        # make sure we have data for each member
        for member in members:
            if member not in data:
                # use join date if it's more recent than oldest
                if member.joined_at > oldest:
                    data[member] = member.joined_at
                else:
                    data[member] = old_af
        # sort members with most inactive 1st
        last_week = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        items = [i for i in sorted(data.items(), key=lambda x: x[1]) if i[1] < last_week]
        lowers = []
        output = []

        for i in items:
            if i[0].top_role == recruit:
                output.append(await self._demote(*i))
            elif i[0].top_role <= recruit:
                if i[0].top_role.name not in ['Lone Wolf']:
                    lowers.append(i)
        await split_send(ctx, output)

        for i in lowers:
            await self._prompt_kick(*i)

        return

    @commands.command()
    async def inactivity(self, ctx, role: discord.Role = None):
        """<role (optional)> shows how long members have been inactive for."""
        await ctx.send("Hold on while I parse the server history.")
        await self._async_init()
        inactive = self.data.file
        if role is not None:
            tmp = [i.id for i in role.members]
            inactive = {i: inactive[i] for i in inactive if i in tmp}
        items = [(ctx.guild.fetch_member(i[0]), _epoch + datetime.timedelta(seconds=i[1]))
                 for i in sorted(inactive.items(), key=lambda x: x[1])]
        msg = ['{0.display_name} {1}'.format(i[0], i[1].date().isoformat())
               for i in items]
        await split_send(ctx, sorted(msg, key=str.lower), style='```')

    @commands.command()
    async def purge(self, ctx, role: discord.Role = None):
        """<role (optional)> shows members that have been inactive for over a week."""
        await ctx.send("Hold on while I parse the server history.")
        await self._async_init()
        inactive = self.data.inactive()
        if role is not None:
            tmp = [i.id for i in role.members]
            inactive = {i: inactive[i] for i in inactive if i in tmp}
        items = [(ctx.guild.fetch_member(i[0]), _epoch + datetime.timedelta(seconds=i[1]))
                 for i in sorted(inactive.items(), key=lambda x: x[1])]
        msg = ['{0.display_name} {1}'.format(i[0], i[1].date().isoformat())
               for i in items]
        await split_send(ctx, sorted(msg, key=str.lower), style='```')

    @commands.command()
    async def purge2(self, ctx, role: discord.Role = None):
        """<role (optional)> shows members that have been inactive for over a week."""
        await ctx.send("Hold on while I parse the server history.")
        await self._async_init()
        recruit = find_role(ctx.guild, "Recruit")
        inactive = self.data.inactive()
        if role is not None:
            tmp = [i.id for i in role.members]
            inactive = {i: inactive[i] for i in inactive if i in tmp}
        items = [(ctx.guild.fetch_member(i[0]), _epoch + datetime.timedelta(seconds=i[1]))
                 for i in sorted(inactive.items(), key=lambda x: x[1])]

        lowers = []
        output = []

        for i in items:
            if i[0].top_role == recruit:
                output.append(await self._demote(*i))
            elif i[0].top_role <= recruit:
                if i[0].top_role.name not in ['Lone Wolf']:
                    lowers.append(i)
        await split_send(ctx, output)

        for i in lowers:
            await self._prompt_kick(*i)

        return

    async def _demote(self, m, dt):
        roles = [r for r in m.roles if r.name not in ['@everyone', 'Nitro Booster']]
        if not self._debug:
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
        self.data.update_activity(payload.userid)
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


def setup(bot):
    """This is required to add this cog to a bot as an extension"""
    bot.add_cog(Activity(bot, debug=True))
