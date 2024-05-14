import discord  # type: ignore # noqa: F401
from discord.ext import commands  # type: ignore
import asyncio
import datetime
import random
import re
from .. import param
from ..config import UserConfig
from ..version import usingV2
from ..async_helpers import sleep, admin_check, split_send
from ..helpers import second, minute, localize
from ..wit_data import WitData, roll, gen_shop, gen_loot
import logging


logger = logging.getLogger('discord.' + __name__)


_channel_id = param.channels.champions_landing


# keywords for player/bot config storage
_bot_key = "tdt.wit"
_msg_key = _bot_key + ".msg"


# time between major wit events
def random_time(nlast=3, add_random=True):
    """Return a random time in seconds. Taken from trick_or_treat.py.
    nlast is the number of votes last time. Times are in seconds."""
    if nlast is None:
        nlast = 5
    if add_random:
        nlast += random.uniform(-1, 1)
    nlast = min(max(1, nlast), 10)
    shape = 22 - 2 * nlast
    scale = -1.4 * nlast + 16.4
    ratio = 5 * (16 - nlast) * 7
    t = (random.weibullvariate(shape, scale) + .5) * ratio
    return min(max(3600, t), 3*3600)


async def safe_send(channel, message):
    if isinstance(message, list):
        return await split_send(channel, message)
    if len(message) < 2000:
        await channel.send(message)
    else:
        tmp = re.split(r"(\.|\n+)", message)
        if not tmp:
            return
        out = [tmp[0]]
        for s in tmp[1:]:
            if s.startswith('.') or s.startswith('\n'):
                out[-1] += s
            else:
                out.append(s)
        chunks = [out[0]]
        for s in out[1:]:
            if len(chunks[-1]) + len(s) < 2000:
                chunks[-1] += s
            else:
                chunks.append(s)
        for s in chunks:
            await channel.send(s)


class Wit(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot
        self._init = False
        self._init_finished = False
        self._active_message_id = None
        self._dt = 60 * minute
        self._channel = None
        self._configs = dict()
        self.data = WitData(parent=self)

        for mid in [param.messages.wit_pvp, param.messages.wit_pve]:
            self.bot.enroll_emoji_role({param.emojis.wit: param.roles.wit_initiate}, message_id=mid)

    def get_data(self, *keys):
        """Retrieve preloaded wit data"""
        return self.data.get_data(*keys)

    def get_command(self, cmd, exicute=True):
        """Get command from wit data files"""
        return self.data.get_command(cmd, exicute=exicute)

    def set_command(self, cmd):
        """Set command in wit data files"""
        async def _(ctx, *args):
            exe = lambda: self.get_command(cmd, exicute=True)  # noqa: E731
            await safe_send(ctx, exe())

        key = cmd[:]
        func = commands.command(name=key)(_)
        setattr(self, key, _)
        self.bot.add_command(func)
        return key

    async def _async_init(self):
        if self._init:
            return
        self._init = True
        self._channel = await self.bot.fetch_channel(_channel_id)
        # await self.send_major()  # no more random major events per Mesome 2024-05-03
        self._init_finished = True

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(5)
        await self._async_init()

    def _get_config(self, user=None):
        """Get a user's config file"""
        if user is None:
            user = self.bot.user
        try:
            return self._configs[user.id]
        except KeyError:
            self._configs[user.id] = UserConfig(user)
            return self._configs[user.id]

    @property
    def message_id(self):
        """Active major id"""
        if self._active_message_id is None:
            try:
                self._active_message_id = self._get_config().set_if_not_set(_msg_key, 0)
            except AttributeError:
                self._active_message_id = None
        return self._active_message_id

    async def message_active(self):
        if not self.message_id:
            return False
        msg = await self._get_message()
        if localize(msg.created_at) < localize(datetime.datetime.utcnow() - self._dt):
            self._set_msg_id(0)
            return False
        return True

    @property
    def channel(self):
        if self._channel is None:
            self._channel = self.bot.find_channel(_channel_id)
        return self._channel

    async def send_major(self, dt=0, set_timer=True):
        """Send wit major"""
        # if we have an active game message already then quit
        if not dt and await self.message_active():
            return
        if dt is True:
            dt = random_time()
            self._dt = dt * second
        await sleep(dt)
        # ensure some funny business didn't happen while we were waiting
        if await self.message_active():
            return
        # send new active game message
        enemies = self.get_data('zones', 'champions_landing', 'enemies').values()
        enemies = [i for i in enemies]
        msg = "# MAJOR\n" + random.choice(enemies)
        msg = await self.channel.send(msg)
        self._set_msg_id(msg.id)
        if set_timer is not True and set_timer < .01:
            set_timer = .01
        if set_timer:
            # launch task for delayed message
            self.bot.loop.create_task(self.send_major(dt=set_timer))

    async def _get_message(self):
        """Get active game message id"""
        if self.message_id:
            try:
                return await self.channel.fetch_message(self.message_id)
            except discord.NotFound:
                self._set_msg_id(0)

    def _set_msg_id(self, idn):
        """set active message id and return old one"""
        old = self.message_id
        self._active_message_id = idn
        self._get_config(self.bot.user)[_msg_key] = idn
        return old

    @commands.command()
    async def wit_shop(self, ctx):
        """Show the wit shop"""
        await split_send(ctx, gen_shop(), "\n\n")

    @commands.command()
    async def wit_loot(self, ctx, roll_str=None):
        """Create a random loot item"""
        await split_send(ctx, gen_loot(roll_str), "\n\n")

    @commands.command(aliases=['r'])
    async def roll(self, ctx, *roll_str):
        roll_str = ' '.join(roll_str)
        rolls = roll(roll_str)
        msg = '{:}\n'.format(ctx.author.mention)
        msg += 'Rolling {:}:\n'.format(roll_str)
        msg += ' + '.join([str(i) for i in rolls])
        if len(rolls) > 1:
            msg += ' = {:}'.format(sum(rolls))
        await ctx.send(msg)
        await ctx.message.delete()

    @commands.check(admin_check)
    @commands.command()
    async def force_major(self, ctx):
        self._dt = 0 * second
        self._set_msg_id(0)
        self._active_message_id = None
        await self.send_major()


if usingV2:
    async def setup(bot):
        cog = Wit(bot)
        await bot.add_cog(cog)
else:
    def setup(bot):
        bot.add_cog(Wit(bot))
