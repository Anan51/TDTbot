import asyncio
import datetime
import discord
from discord.ext import commands
import random
from .. import param
from ..helpers import *
from ..config import UserConfig
from ..async_helpers import split_send, wait_until
import logging


logger = logging.getLogger('discord.' + __name__)

_trick = "😈"
_treat = "🍬"
_start = 0
_score = "tdt.trick_or_treat.score"
_msg = "Trick ({:}) or Treat ({:})!".format(_trick, _treat)
_bot = 'tdt.trick_or_treat.msg'
_role = 'trick or treat'
_tmin, _tmax = 60 * 5, 3600 * 2
_tmin, _tmax = 5, 60


class TrickOrTreat(commands.Cog):
    """Cog for trick or treat game"""
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self.channel = self.bot.find_channel(param.rc('log_channel'))
        self._configs = dict()
        self._init = False
        self._active_message_id = self._get_config(self.bot.user).set_if_not_set(_bot, 0)

    def cog_check(self, ctx):
        return ctx.channel == self.channel

    async def send_message(self, dt=0, set_timer=True):
        if self._active_message_id:
            return
        if dt is True:
            dt = random.randint(_tmin, _tmax)
        await asyncio.sleep(dt)
        msg = self.channel.send(_msg)
        self._set_msg_id(msg.id)
        await msg.add_reaction(_trick)
        await msg.add_reaction(_treat)
        if set_timer == 0:
            set_timer = .01
        if set_timer:
            self.cog.bot.loop.create_task(self.finish_count(dt=set_timer, mid=msg.id))

    def send_later(self, **kwargs):
        self.cog.bot.loop.create_task(self.send_message(**kwargs))

    async def _get_message(self):
        if self._active_message_id:
            try:
                return await self.channel.fetch_message(self._active_message_id)
            except discord.NotFound:
                self._set_msg_id(0)

    def _set_msg_id(self, idn):
        old = self._active_message_id
        self._active_message_id = idn
        self._get_config(self.bot.user)[_bot] = idn
        return old

    def _get_config(self, user):
        try:
            return self._configs[user.id]
        except KeyError:
            self._configs[user.id] = UserConfig(user)
            return self._configs[user.id]

    def apply_delta(self, user, delta):
        config = self._get_config(user)
        old = config.set_if_not_set(_score, _start)
        config[_score] += delta
        return old, delta, old + delta

    def get_score(self, user):
        return self._get_config(user).set_if_not_set(_score, _start)

    async def finish_count(self, dt=0, set_timer=True, mid=0):
        if dt is True:
            dt = random.randint(_tmin, _tmax)
        await asyncio.sleep(dt)
        msg = await self._get_message()
        if not msg:
            if set_timer:
                return self.send_message()
        if msg.id != mid:
            return
        trickers = []
        treaters = []
        ntrick, ntreat = 0, 0
        for rxn in msg.reactions():
            if rxn.emoji == _trick:
                ntrick = rxn.count
                trickers = [user async for user in rxn.users() if user != self.bot.user]
            elif rxn.emoji == _treat:
                ntreat = rxn.count
                treaters = [user async for user in rxn.users() if user != self.bot.user]
            else:
                try:
                    await rxn.clear()
                except discord.HTTPException:
                    pass
        if not trickers and not treaters:
            return self.count_later(dt=set_timer, mid=mid)
        results = ' {:}{:} vs {:}{:}'.format(ntrick, _trick, ntreat, _treat)
        if ntrick > ntreat:
            dtrick = 0
            dtreat = -2
            txt = "The tricksters have won:"
        elif ntrick < ntreat:
            dtrick = 0
            dtreat = 1
            txt = "The treaters get a treat!"
        else:
            dtrick = 0
            dtreat = 0
            txt = "Tied voting."
        txt += results
        deltas = {user.id: dtrick for user in trickers}
        for user in treaters:
            deltas[user] = deltas.get(user, 0) + dtreat
        users = sorted(deltas.keys(), key=lambda u: u.display_name)
        fmt = "{0.display_name} : {1:d}{2:+d} => {3:d} (current)"
        summary = [fmt.format(u, *self.apply_delta(u, deltas[u.id]))
                   for u in users if deltas[u.id]]
        await self.channel.send(txt)
        await split_send(self.channel, summary, style='```')
        self._set_msg_id(0)
        if set_timer is 0:
            set_timer = .01
        if set_timer:
            self.send_later(dt=set_timer)

    def count_later(self, **kwargs):
        self.cog.bot.loop.create_task(self.finish_count(**kwargs))

    @commands.Cog.listener()
    async def on_message(self, message):
        """Parse messages for new event post"""
        # ignore all messages from our bot
        if message.author == self.bot.user:
            return
        if not self._init:
            self._init = True
            if not await self._get_message():
                await self.send_message()
        if not self._active_message_id:
            await self.send_message()

    @commands.command()
    async def show_points(self, ctx, member: discord.Member = None):
        """<member (optional)> shows trick or treat points"""
        if member is None:
            member = ctx.author
        txt = "{:} has {:} points.".format(member, self.get_score(member))

    @commands.command()
    async def rankings(self, ctx):
        role = find_role(ctx.guild, _role)
        data = {m: self.get_score(m) for m in role.members}
        users = sorted(data.keys(), key=lambda u: (data[u], u.display_name))
        summary = ['{0.display_name} : {1}'.format(u, data[u]) for u in users]
        await split_send(self.channel, summary, style='```')


def setup(bot):
    bot.add_cog(TrickOrTreat(bot))
