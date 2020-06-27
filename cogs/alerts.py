import discord
from discord.ext import commands
from .. import param
from ..helpers import *


class Alerts(commands.Cog):
    """Cog to listen and send alerts"""
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Alert admin type roles on new member joining"""
        channel = self.bot.find_channel(param.rc('log_channel'))
        roles = [find_role(member.guild, i) for i in ["Admin", "Devoted"]]
        roles = " ".join([i.mention for i in roles if hasattr(i, 'mention')])
        print(member, roles, channel)
        if channel is not None:
            await channel.send(roles + ' new member {0.name} joined.'.format(member))


def setup(bot):
    bot.add_cog(Alerts(bot))
