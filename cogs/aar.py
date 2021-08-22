import datetime
import discord
from discord.ext import commands
import logging
import pytz
from ..async_helpers import git_log
from ..helpers import *
from .. import param


logger = logging.getLogger('discord.' + __name__)
_tz = pytz.timezone(param.rc('timezone'))
_day = datetime.timedelta(days=1)


class AAR(commands.Cog):
    """Cog designed to handel Stellar's AAR, cause he's lazy"""
    channel = 481904729597935626

    def __init__(self, bot):
        self.bot = bot
        self._last_post = None

    @commands.Cog.listener()
    async def on_message(self, message):
        """Parse messages for Mesome asking for AARs"""
        # if not devoted_chat channel
        if message.channel.id != self.channel:
            return
        # if not Mesome, return
        try:
            if message.author != message.guild.owner:
                return
        except AttributeError:
            return
        if 'aar' not in message.content.lower():
            return
        # if we posted an AAR in the last day, return
        if self._last_post is not None:
            if datetime.datetime.utcnow() - self._last_post < _day:
                return
        # assign UTC timezone to message creation timestamp
        dt = pytz.utc.localize(message.created_at)
        # convert to server timezone
        dt = dt.astimezone(_tz)
        # if it is not sunday return
        if dt.today().weekday() != 6:
            return
        # Now it is time to print Stellar's AAR
        await message.channel.send("Stellar's AAR:")
        await git_log(message.channel)
        self._last_post = datetime.datetime.utcnow()


def setup(bot):
    bot.add_cog(AAR(bot))
