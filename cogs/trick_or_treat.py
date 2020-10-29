import asyncio
import datetime
import discord
from discord.ext import commands
import random
from .. import param
from ..helpers import *
from ..config import UserConfig
from ..async_helpers import split_send
import logging


logger = logging.getLogger('discord.' + __name__)

_trick = "😈"
_treat = "🍬"
_channel = "the_neighborhood"
_start = 0
_score = "tdt.trick_or_treat.score"
_msg = "Trick ({:}) or Treat ({:})!".format(_trick, _treat)
_bot = 'tdt.trick_or_treat.msg'
_role = 'SPOOKY'
_tmin, _tmax = 5 * 60, 15 * 60
_rule_id = 770363043515203604


class TrickOrTreat(commands.Cog):
    """Cog for trick or treat game"""
    def __init__(self, bot):
        logger.printv('TrickOrTreat.__init__')
        self.bot = bot
        self._last_member = None
        self._configs = dict()
        self._init = False
        self._active_message_id = None
        self._awaiting = None
        self._last = datetime.datetime.now()
        logger.printv('Finished TrickOrTreat.__init__')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Parse reaction adds for agreeing to code of conduct and rank them up to
        Recruit"""
        # if not code of conduct message
        if payload.message_id != _rule_id:
            return
        if str(payload.emoji) == "🎃":
            await payload.member.add_roles(self.role)

    @property
    def role(self):
        return find_role(self.channel.guild, _role)

    @property
    def channel(self):
        return self.bot.find_channel(_channel)

    @property
    def message_id(self):
        logger.printv('TrickOrTreat.message_id')
        if self._active_message_id is None:
            try:
                self._active_message_id = self._get_config(self.bot.user).set_if_not_set(_bot, 0)
            except AttributeError:
                self._active_message_id = None
        return self._active_message_id

    def cog_check(self, ctx):
        return ctx.channel == self.channel

    async def send_message(self, dt=0, set_timer=True):
        if dt is True:
            dt = random.randint(_tmin, _tmax)
        logger.printv('TrickOrTreat.send_message waiting for {:} s'.format(dt))
        if self.message_id:
            return
        if self._awaiting:
            return
        await asyncio.sleep(dt)
        if self.message_id:
            return
        if self._awaiting:
            return
        msg = await self.channel.send(_msg)
        self._set_msg_id(msg.id)
        await msg.add_reaction(_trick)
        await msg.add_reaction(_treat)
        if set_timer == 0:
            set_timer = .01
        if set_timer:
            self.bot.loop.create_task(self.finish_count(dt=set_timer, mid=msg.id))

    def send_later(self, **kwargs):
        logger.printv('TrickOrTreat.send_later')
        self.bot.loop.create_task(self.send_message(**kwargs))

    async def _get_message(self):
        logger.printv('TrickOrTreat._get_message')
        if self.message_id:
            try:
                return await self.channel.fetch_message(self.message_id)
            except discord.NotFound:
                self._set_msg_id(0)

    def _set_msg_id(self, idn):
        logger.printv('TrickOrTreat._set_msg_id')
        old = self.message_id
        self._active_message_id = idn
        self._get_config(self.bot.user)[_bot] = idn
        return old

    def _get_config(self, user):
        logger.printv('TrickOrTreat._get_config')
        try:
            return self._configs[user.id]
        except KeyError:
            self._configs[user.id] = UserConfig(user)
            return self._configs[user.id]

    def apply_delta(self, user, delta):
        logger.printv('TrickOrTreat.apply_delta')
        config = self._get_config(user)
        old = config.set_if_not_set(_score, _start)
        config[_score] += delta
        return old, delta, old + delta

    def get_score(self, user):
        logger.printv('TrickOrTreat.get_score')
        return self._get_config(user).set_if_not_set(_score, _start)

    async def _member(self, user):
        try:
            out = [m for m in self.role.members if m.id == user.id]
            if out:
                return out[0]
        except AttributeError:
            pass
        try:
            out = self.channel.guild.fetch_member(user.id)
            if not out:
                return user
        except discord.HTTPException:
            pass
        out = self.channel.guild.get_member_named(user.name)
        if out:
            return out
        return user

    async def finish_count(self, dt=0, set_timer=True, mid=0):
        if dt is True:
            dt = random.randint(_tmin, _tmax)
        logger.printv('TrickOrTreat.finish_count waiting for {:} s'.format(dt))
        if self._awaiting is None:
            self._awaiting = mid
        await asyncio.sleep(dt)
        msg = await self._get_message()
        if not msg:
            if set_timer:
                logger.printv('Finish TrickOrTreat.finish_count (no message)')
                self._awaiting = None
                return await self.send_message(dt=set_timer)
        if msg.id != mid:
            logger.printv('Finish TrickOrTreat.finish_count (bad id)')
            self._awaiting = None
            return
        trickers = []
        treaters = []
        ntrick, ntreat = 0, 0
        for rxn in msg.reactions:
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
            logger.printv('Finish TrickOrTreat.finish_count (no votes)')
            self._awaiting = None
            return self.count_later(dt=set_timer, mid=mid)
        ntrick -= 1
        ntreat -= 1
        results = ' {:} x {:} vs {:} x {:}'
        results = results.format(ntrick, _trick, ntreat, _treat)
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
        trickers = [await self._member(u) for u in trickers]
        treaters = [await self._member(u) for u in treaters]
        deltas = {user: dtrick for user in trickers}
        for user in treaters:
            deltas[user] = deltas.get(user, 0) + dtreat
        users = sorted(deltas.keys(), key=lambda u: u.display_name)
        fmt = "{0.display_name} : {1:d}{2:+d} => {3:d} (current)"
        summary = [fmt.format(u, *self.apply_delta(u, deltas[u]))
                   for u in users if deltas[u]]
        print("summary", summary)
        await self.channel.send(txt)
        await split_send(self.channel, summary, style='```')
        self._set_msg_id(0)
        if set_timer == 0:
            set_timer = .01
        if set_timer:
            self.send_later(dt=True)
        self._awaiting = None
        self._last = datetime.datetime.now()
        logger.printv('Finish TrickOrTreat.finish_count (end)')

    def count_later(self, **kwargs):
        logger.printv('TrickOrTreat.channel')
        self.bot.loop.create_task(self.finish_count(**kwargs))

    @commands.Cog.listener()
    async def on_message(self, message):
        """Parse messages for new event post"""
        # ignore all messages from our bot
        if message.author == self.bot.user:
            print("ignoring self")
            return
        if not self._init:
            self._init = True
            if not await self._get_message():
                await self.send_message()
                return
            else:
                self.count_later(dt=True, mid=self.message_id)
        if not self.message_id:
            if datetime.datetime.now() - self._last > datetime.timedelta(minutes=15):
                await self.send_message()
                return
        if not self._awaiting:
            self.count_later(mid=self.message_id)

    @commands.command()
    async def show_points(self, ctx, member: discord.Member = None):
        """<member (optional)> shows trick or treat points"""
        logger.printv('TrickOrTreat.show_points')
        if member is None:
            member = ctx.author
        txt = "{:} has {:} points.".format(member.display_name, self.get_score(member))
        await ctx.send(txt)
        logger.printv('Finished TrickOrTreat.show_points')

    @commands.command(hidden=True)
    async def print_id(self, ctx):
        """Print current message id"""
        await ctx.send(str(self.message_id))

    @commands.command(hidden=True)
    async def _old_rankings(self, ctx):
        """Show current rankings for trick or treat"""
        logger.printv('TrickOrTreat.rankings')
        await ctx.send("This command is currently broken")
        role = self.role
        data = {m: self.get_score(m) for m in role.members}
        users = sorted(data.keys(), key=lambda u: (data[u], u.display_name))
        summary = ['{0.display_name} : {1}'.format(u, data[u]) for u in users]
        print(role, data, role.members, self.channel.guild)
        await split_send(self.channel, summary, style='```')

    @commands.command()
    async def rankings(self, ctx):
        configs = await self.bot.get_user_configs()
        players = [c for c in configs if _score in c]
        data = {self._member(p): p[_score] for p in players}
        users = sorted(data.keys(), key=lambda u: (data[u], u.display_name))
        summary = ['{0.display_name} : {1}'.format(u, data[u]) for u in users]
        print(role, data, role.members, self.channel.guild)
        await split_send(self.channel, summary, style='```')

    @commands.command(hidden=True)
    async def set_score(self, ctx, n: int, member: discord.Member = None):
        if ctx.author != self.bot.owner:
            raise PermissionError("Only {:} can use this command.".format(self.bot.owner))
        if member is None:
            member = ctx.author
        UserConfig(member)[_score] = n
        await ctx.send('Set score of {:} to {:}.'.format(member, n))

def setup(bot):
    bot.add_cog(TrickOrTreat(bot))
