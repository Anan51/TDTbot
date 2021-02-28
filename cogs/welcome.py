import datetime
import discord
from discord.ext import commands
from .. import param
from ..helpers import *
from ..async_helpers import admin_check
import logging


logger = logging.getLogger('discord.' + __name__)
_CoC_id = 563406038754394112


async def send_welcome(member):
    """Sends welcome message to member"""
    msg = 'Greetings {0.name}! Part of my duties as TDTbot are to welcome ' \
          'newcomers to The Dream Team. \n\nSo welcome!\n\nWe have a few questions ' \
          'we ask everyone, so please post the answers to the following questions ' \
          'in the general chat:\n' \
          '1) How did you find out about TDT?\n' \
          '2) What games and platforms do you play?\n' \
          '3) Are you a YouTube subscriber? If so, are you a channel member?\n\n'\
          'If you\'re interested in learning wolf pack (see our #manual_page), ping ' \
          '@member.\n\n'\
          'And... finally... we have a code of conduct in our #manual_page that we ' \
          'ask everybody to agree to. Just give it a 👍 if you agree. If you want me to ' \
          'give you a Destiny 2 tag, click the corresponding platform tag on the ' \
          'code of conduct after you give the thumbs up.' \
          '\n\nWhelp, I hope someone gives you a less robotic welcome soon!\n\n'\
          'Also find us on social media:\n'\
          'YT channel membership: https://www.youtube.com/channel/UCKBCsmU53MBzCm_wNZY7hLA/join\n'\
          'Twitter: https://twitter.com/productions_tdt\n'\
          'Instagram: https://www.instagram.com/tdt_productions_'
    channel = member.dm_channel
    if not channel:
        await member.create_dm()
        channel = member.dm_channel
    await channel.send(msg.format(member))


class Welcome(commands.Cog):
    """Cog to listen and send alerts"""
    _emoji_dict = {350189008078372865: "PSN D2",
                   641083615387713567: "Xbox D2",
                   641083208871706664: "D2 PC",
                   646219746886418452: "Stadia D2"
                   }

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
        manual = self.bot.find_channel("manual_page")
        msg = "Welcome to TDT {0.mention} <a:blobDance:738431916910444644>" \
              " Please read my DM and look at the {1.mention}.".format(member, manual)
        await member.guild.system_channel.send(msg)

    @commands.command()
    async def send_welcome(self, ctx, member: discord.User = None):
        """Send welcome message to an individual for testing"""
        if not member:
            member = ctx.author
        await send_welcome(member)

    async def _emoji2role(self, payload, emoji=None):
        if emoji is None:
            emoji = payload.emoji
        try:
            eid = emoji.id
        except AttributeError:
            eid = str(emoji)
        guild = [g for g in self.bot.guilds if g.id == payload.guild_id][0]
        try:
            role = find_role(guild, self._emoji_dict[eid])
            if payload.member.top_role >= find_role(guild, "Recruit"):
                await payload.member.add_roles(role)
        except KeyError:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Parse reaction adds for agreeing to code of conduct and rank them up to
        Recruit"""
        # if not code of conduct message
        if payload.message_id != _CoC_id:
            return
        if str(payload.emoji) == "👍":
            out = "{0.display_name} agreed to the code of conduct.".format(payload.member)
            logger.printv(out)
            guild = [g for g in self.bot.guilds if g.id == payload.guild_id][0]
            log_channel = find_channel(guild, "admin_log")
            # if they've agreed to CoC recently then return
            async for msg in log_channel.history(limit=200):
                if msg.content == out:
                    return
            await log_channel.send(out)
            now = datetime.datetime.utcnow()
            # if in joined in last 2 weeks
            if (now - payload.member.joined_at).seconds // 86400 < 14:
                role = find_role(guild, "Recruit")
                if payload.member.top_role < role:
                    reason = "Agreed to code of conduct."
                    await payload.member.add_roles(role, reason=reason)
                # if they reacted before this with a platform role
                channel = self.bot.find_channel("manual_page")
                msg = await channel.fetch_message(_CoC_id)
                for rxn in msg.reactions:

                    if getattr(rxn.emoji, 'id', rxn.emoji) in self._emoji_dict:
                        if payload.member in await rxn.users().flatten():
                            await self._emoji2role(payload, emoji=rxn.emoji)
            return
        if hasattr(payload.emoji, 'id'):
            await self._emoji2role(payload)

    # todo: welcome back


def setup(bot):
    bot.add_cog(Welcome(bot))
