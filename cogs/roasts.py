import datetime
import discord
from discord.ext import commands
import logging
import random
import re
import sys
from .. import param
from ..helpers import *
from ..async_helpers import admin_check


logger = logging.getLogger('discord.' + __name__)
_m_delete = discord.AuditLogAction.message_delete
_min = datetime.timedelta(seconds=60)


def roast_str():
    """Randomly pull a roast from the roasts list"""
    return random.choice(param.rc('roasts'))


class Roast(commands.Cog):
    """Cog to roast people"""
    def __init__(self, bot):
        self.bot = bot
        self._nemeses = [i for i in param.rc('nemeses')]
        self._last_roast = None
        self._snipes = dict()
        self._roasts = []

    def _log_roast(self, mid):
        while sys.getsizeof(self._roasts) > 1048576:
            self._roasts.pop(0)
        self._roasts.append(mid)

    async def _send_roast(self, channel, prefix=None):
        msg = roast_str()
        if prefix is not None:
            msg = prefix.rstrip() + ' ' + channel
        msg = await channel.send(msg)
        self._log_roast(msg.id)

    @commands.command(aliases=['burn'])
    async def roast(self, ctx, channel: str = None, guild: str = None):
        """<channel (optional)> <server (optional)> sends random roast message"""
        if guild is None:
            guild = ctx.guild
        else:
            try:
                guild = [i for i in self.bot.guilds if i.name == guild][0]
            except IndexError:
                ctx.send('ERROR: server "{0}" not found.'.format(guild))
                return
        if channel:
            channel = find_channel(guild, channel)
        else:
            channel = ctx.channel
        self._last_roast = await channel.fetch_message(channel.last_message_id)
        await self._send_roast(channel)

    @commands.command()
    async def nou(self, ctx, channel: str = None, guild: str = None):
        """<channel (optional)> <server (optional)> NO U"""
        if guild is None:
            guild = ctx.guild
        else:
            try:
                guild = [i for i in self.bot.guilds if i.name == guild][0]
            except IndexError:
                ctx.send("NO U (need to type a reasonable server name)")
                return
        if channel:
            channel = find_channel(guild, channel)
        else:
            channel = ctx.channel
        await channel.send("NO U")

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        if payload.message_id in self._roasts:
            now = datetime.datetime.utcnow()
            guild = await self.bot.fetch_guild(payload.guild_id)
            opt = dict(action=_m_delete, after=now - _min)
            out = []
            async for entry in guild.audit_logs(**opt):
                if entry.target == guild.me:
                    if entry.extra.channel.id == payload.channel_id:
                        if entry.user not in [self.bot.owner, guild.owner]:
                            out.append([entry.user, abs(now - entry.created_at)])
            if out:
                user = sorted(out, key=lambda x: x[1])[0][0]
                channel = await guild.fetch_channel(payload.channel_id)
                await self._send_roast(channel, prefix=user.mention)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Parse messages to see if we should roast even without a command"""
        # ignore commands
        try:
            if message.content.startswith(self.bot.command_prefix):
                return
        except TypeError:
            for prefix in self.bot.command_prefix:
                if message.content.startswith(prefix):
                    return
        # ignore messages from this bot
        if message.author == self.bot.user:
            return
        # if author in snipes
        try:
            self._snipes[message.author.id] -= 1
            if self._snipes[message.author.id] <= 0:
                self._snipes.pop(message.author.id)
            await message.channel.send(roast_str())
            self._last_roast = message
        except KeyError:
            pass
        # set a trigger list for sending roasts
        triggers = ['<:lenny:333101455856762890> <:OGTriggered:433210982647595019>']
        # if some trigger then roast
        if message.content.strip() in triggers:
            if not random.randrange(3):
                logger.debug('Ignoring trigger')
                return
            await message.channel.send(roast_str())
            self._last_roast = message
            return
        if '🍞' in message.content.strip():
            if not random.randrange(3):
                logger.debug('Ignoring trigger')
            else:
                await message.channel.send(roast_str())
                self._last_roast = message
                return
        # respond to any form of REEE
        if re.match('^[rR]+[Ee][Ee]+$', message.content.strip()):
            r = random.randrange(7)
            if r < 2:
                logger.debug('Ignoring trigger')
                return
            if r < 4:
                await message.channel.send("NO U")
            else:
                await message.channel.send(roast_str())
            self._last_roast = message
            return
        old = self._last_roast
        if old:
            # if the message author is the last person we roasted and in the same channel
            if message.author == old.author and message.channel == old.channel:
                # if this message is < 1 min from the last one
                if (message.created_at - old.created_at).total_seconds() < 120:
                    if message.content.lower().strip() in ['omg', 'bruh']:
                        await message.channel.send(roast_str())
                        self._last_roast = None
                        return
                    self._last_roast = None
        # if the nemesis of this bot posts a non command message
        try:
            if message.author.id in self._nemeses:
                logger.printv('Nemesis: {0.author}'.format(message))
                # if nemesis posts boomer type word
                if re.findall('[bz]oome[rt]', message.content.lower()):
                    logger.debug('[bz]oome[rt]')
                    if random.randrange(2):
                        logger.debug('Ignoring trigger')
                        return
                    if not random.randrange(3):  # 1/3 prob
                        logger.debug('roast')
                        await message.channel.send(roast_str())
                    else:  # 2/3 prob
                        logger.debug('no u')
                        await message.channel.send("NO U")
                    self._last_roast = message
                    return
                # regex list of triggers
                matches = ['your m[ao]m', 'shut it bot']
                for m in matches:
                    if random.randrange(2):
                        logger.debug('Ignoring trigger')
                        return
                    if re.findall(m, message.content.lower()):
                        logger.debug('Nemesis message matched "{:}"'.format(m))
                        await message.channel.send(roast_str())
                        self._last_roast = message
                        return
                # Roast nemesis with 1/30 probability
                if not random.randrange(30):
                    logger.printv("Decided to roast nemesis.")
                    await message.channel.send(roast_str())
                    self._last_roast = message
                    return
        # catch self._nemeses = None
        except TypeError:
            pass
        return

    @commands.command(hidden=True)
    @commands.check(admin_check)
    async def roast_snipe(self, ctx, user: discord.User, n: int = 1):
        self._snipes[user.id] = n + self._snipes.get(user.id, 0)
        if self._snipes[user.id] <= 0:
            self._snipes.pop(user.id)


def setup(bot):
    bot.add_cog(Roast(bot))
