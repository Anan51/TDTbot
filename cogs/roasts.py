import discord
from discord.ext import commands
import random
import re
from .. import param
from ..helpers import *


def roast_str():
    """Randomly pull a roast from the roasts list"""
    return random.choice(param.rc('roasts'))


class Roast(commands.Cog):
    """Cog to roast people"""
    def __init__(self, bot):
        self.bot = bot
        self._nemeses = param.rc('nemeses')
        self._last_roast = None

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
        await channel.send(roast_str())

    @commands.Cog.listener()
    async def on_message(self, message):
        """Parse messages to see if we should roast even without a command"""
        # ignore commands
        if message.content.startswith(self.bot.command_prefix):
            return
        # ignore messages from this bot
        if message.author == self.bot.user:
            return
        # set a trigger list for sending roasts
        triggers = ['<:lenny:333101455856762890> <:OGTriggered:433210982647595019>']
        # if some form of REEE or a trigger than roast
        if (re.match('^[rR]+[Ee][Ee]+$', message.content.strip())
                or message.content.strip() in triggers):
            await message.channel.send(roast_str())
            self._last_roast = message
            return
        old = self._last_roast
        if old:
            # if the message author is the last person we roasted and in the same channel
            if message.author == old.author and message.channel == old.channel:
                # if this message is < 1 min from the last one
                if (message.created_at - old.created_at).total_seconds() < 60:
                    if message.content.lower().strip() in ['omg', 'bruh']:
                        await message.channel.send(roast_str())
                        self._last_roast = None
                        return
                    self._last_roast = None
        # if the nemesis of this bot posts a non command message then roast them with
        # 1/20 probability
        try:
            if message.author.name in self._nemeses:
                if not random.randrange(20):
                    await message.channel.send(roast_str())
                    self._last_roast = message.author
        except TypeError:
            pass
        return


def setup(bot):
    bot.add_cog(Roast(bot))
