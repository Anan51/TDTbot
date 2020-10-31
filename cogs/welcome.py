import datetime
import discord
from discord.ext import commands
from .. import param
from ..helpers import *
import logging


logger = logging.getLogger('discord.' + __name__)


async def send_welcome(member):
    """Sends welcome message to member"""
    msg = 'Greetings {0.name}! Part of my duties as TDTbot are to welcome ' \
          'newcomers to The Dream Team. \n\nSo welcome!\n\nWe have a few questions ' \
          'we ask everyone, so please post the answers to the following questions ' \
          'in the general chat:\n' \
          '1) How did you find out about TDT?\n' \
          '2) What games and platforms do you play?\n' \
          '3) What is you main in-game-name?\n\n' \
          'If you\'re interested in learning wolf pack (see our #manual_page), ping ' \
          '@member.\n\n'\
          'And... finally... we have a code of conduct in our #manual_page that we ' \
          'ask everybody to agree to. Just give it a 👍 if you agree. If you want me to ' \
          'give you a Destiny 2 tag, click the corresponding platform tag on the ' \
          'code of conduct after you give the thumbs up.\n\n' \
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
        logger.printv('New member {0.name} joined'.format(member))
        channel = self.bot.find_channel(param.rc('log_channel'))
        roles = [find_role(member.guild, i) for i in ["Admin", "Devoted"]]
        roles = " ".join([i.mention for i in roles if hasattr(i, 'mention')])
        if channel is not None:
            await channel.send(roles + ' new member {0.name} joined.'.format(member))
        await send_welcome(member)
        msg = "Welcome to TDT {0.mention} <a:blobDance:738431916910444644>" \
              " Please read my DM.".format(member)
        await member.guild.system_channel.send(msg)

    @commands.command(hidden=True)
    async def test_welcome(self, ctx, member: discord.User = None):
        """Send welcome message to an individual for testing"""
        if not member:
            member = ctx.author
        await send_welcome(member)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Parse reaction adds for agreeing to code of conduct and rank them up to
        Recruit"""
        # if not code of conduct message
        if payload.message_id != 563406038754394112:
            return
        if str(payload.emoji) == "👍":
            out = "{0.display_name} agreed to the code of conduct.".format(payload.member)
            logger.printv(out)
            guild = [g for g in self.bot.guilds if g.id == payload.guild_id][0]
            log_channel = find_channel(guild, "admin_log")
            # if they've agreed to CoC recently
            async for msg in log_channel.history(limit=200):
                if msg.content == out:
                    return
            await log_channel.send(out)
            now = datetime.datetime.utcnow()
            # if in joined in last 2 weeks
            if (now - payload.member.joined_at).seconds // 86400 < 14:
                role = find_role(guild, "Recruit")
                if payload.member.top_role < role:
                    reason = "Agreed to cod of conduct."
                    await payload.member.add_roles(role, reason=reason)
            return
        if hasattr(payload.emoji, 'id'):
            role = None
            guild = [g for g in self.bot.guilds if g.id == payload.guild_id][0]
            if payload.emoji.id == 350189008078372865:
                role = find_role(guild, "PSN D2")
            if payload.emoji.id == 641083615387713567:
                role = find_role(guild, "Xbox D2")
            if payload.emoji.id == 641083208871706664:
                role = find_role(guild, "D2 PC")
            if role is not None:
                if payload.member.top_role >= find_role(guild, "Recruit"):
                    await payload.member.add_roles(role)


def setup(bot):
    bot.add_cog(Welcome(bot))
