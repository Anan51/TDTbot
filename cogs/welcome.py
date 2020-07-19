import discord
from discord.ext import commands
from .. import param
from ..helpers import *


async def send_welcome(member):
    """Sends welcome message to member"""
    msg = 'Greetings {0.name}! Part of my duties as TDTbot are to welcome ' \
          'newcomers to The Dream Team. \n\nSo welcome!\n\nWe have a few questions ' \
          'we ask everyone, so please post the answers to the following questions ' \
          'in the general chat:\n' \
          '1) How did you find out about TDT?\n' \
          '2) What games and platforms do you play?\n' \
          '3) What is you main in-game-name?\n\n' \
          'And... finally... we have a code of conduct in our #manual_page that we ' \
          'ask everybody to agree to. Just give it a 👍 if you agree.\n\n' \
          'Whelp, that\'s it! I hope someone gives you a less robotic welcome soon!'
    channel = member.dm_channel
    if not channel:
        await member.create_dm()
        channel = member.dm_channel
    await channel.send(msg.format(member))


class Welcome(commands.Cog):
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
        if channel is not None:
            await channel.send(roles + ' new member {0.name} joined.'.format(member))
        # await send_welcome(member)

    @commands.command(hidden=True)
    async def test_welcome(self, ctx, member: discord.User = None):
        if not member:
            member = ctx.author
        await send_welcome(member)

    @commands.Cog.listener()
    async def on_reaction_add(self, rxn, user):
        if not rxn.message.content.startswith('CODE OF CONDUCT'):
            return
        msg = "{0.display_name} agreed to the code of conduct.".format(user)
        log_channel = find_channel(rxn.message.guild, "admin_log")
        async for msg in log_channel.history(limit=200):
            if msg.content == msg:
                return
        await self.log_channel.send(msg)


def setup(bot):
    bot.add_cog(Welcome(bot))
