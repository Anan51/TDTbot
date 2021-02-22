import datetime
import discord
from discord.ext import commands
import logging
from .. import param
from ..helpers import *
from ..async_helpers import *


logger = logging.getLogger('discord.' + __name__)


class MainCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self._kicks = []

    @commands.command()
    async def guild(self, ctx):
        """Prints guild/server name."""
        await ctx.channel.send(ctx.guild.name)

    @commands.command()
    async def hello(self, ctx, *, member: discord.Member = None):
        """<member (optional)> Says hello"""
        member = member or ctx.author
        if self._last_member is None or self._last_member.id != member.id:
            await ctx.send('Hello {0.name}!'.format(member))
        else:
            await ctx.send('Hello {0.name}... This feels familiar.'.format(member))
        self._last_member = member

    @commands.command()
    async def inactivity(self, ctx, role: discord.Role = None):
        """<role (optional)> shows how long members have been inactive for."""
        await ctx.send("Hold on while I parse the server history.")
        if role is None:
            members = ctx.guild.members
        else:
            members = role.members
        data = dict()
        # get all channels with a history attribute
        channels = [i for i in ctx.guild.channels if hasattr(i, "history")]
        oldest = datetime.datetime.now()  # store the oldest time parsed
        old_af = datetime.datetime(1, 1, 1)  # just some really old date
        for channel in channels:
            try:
                # loop through messages in history (limit 1000 messages per channel)
                async for msg in channel.history(limit=1000):
                    # update oldest
                    oldest = min(oldest, msg.created_at)
                    # add/update data for message author
                    if msg.author in members:
                        try:
                            # use the most recent date
                            data[msg.author] = max(data[msg.author], msg.created_at)
                        except KeyError:
                            data[msg.author] = msg.created_at
            except discord.Forbidden:
                # We do not have permission to read this channel's history
                # await ctx.send("Cannot read channel {0}.".format(channel))
                pass
        # make sure we have data for each member
        for member in members:
            if member not in data:
                # use join date if it's more recent than oldest
                if member.joined_at > oldest:
                    data[member] = member.joined_at
                else:
                    data[member] = old_af
        # sort members with most inactive 1st
        items = sorted(data.items(), key=lambda x: x[1])
        msg = ['{0.display_name} {1}'.format(i[0], i[1].date().isoformat())
               for i in items]
        await split_send(ctx, msg, style='```')

    @commands.command()
    async def purge(self, ctx, role: discord.Role = None):
        """<role (optional)> shows members that have been inactive for over a week."""
        await ctx.send("Hold on while I parse the server history.")
        if role is None:
            members = ctx.guild.members
        else:
            members = role.members
        data = dict()
        # get all channels with a history attribute
        channels = [i for i in ctx.guild.channels if hasattr(i, "history")]
        oldest = datetime.datetime.now()  # store the oldest time parsed
        old_af = datetime.datetime(1, 1, 1)  # just some really old date
        for channel in channels:
            try:
                # loop through messages in history (limit 1000 messages per channel)
                async for msg in channel.history(limit=1000):
                    # update oldest
                    oldest = min(oldest, msg.created_at)
                    # add/update data for message author
                    if msg.author in members:
                        try:
                            # use the most recent date
                            data[msg.author] = max(data[msg.author], msg.created_at)
                        except KeyError:
                            data[msg.author] = msg.created_at
            except discord.Forbidden:
                # We do not have permission to read this channel's history
                # await ctx.send("Cannot read channel {0}.".format(channel))
                pass
        # make sure we have data for each member
        for member in members:
            if member not in data:
                # use join date if it's more recent than oldest
                if member.joined_at > oldest:
                    data[member] = member.joined_at
                else:
                    data[member] = old_af
        # sort members with most inactive 1st
        last_week = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        items = [i for i in sorted(data.items(), key=lambda x: x[1]) if i[1] < last_week]

        msg = ['{0.display_name} {1}'.format(i[0], i[1].date().isoformat())
               for i in items]
        await split_send(ctx, sorted(msg, key=str.lower), style='```')

    @commands.command()
    @commands.check(admin_check)
    async def purge2(self, ctx):
        """<role (optional)> demote (kick) recruits (rankless) who've been inactive for a
        week."""
        await ctx.send("Hold on while I parse the server history.")
        recruit = find_role(ctx.guild, "Recruit")
        members = []
        async for member in ctx.guild.fetch_members(limit=2000):
            if not member.bot:
                if member.top_role <= recruit:
                    members.append(member)
        data = dict()
        # get all channels with a history attribute
        channels = [i for i in ctx.guild.channels if hasattr(i, "history")]
        oldest = datetime.datetime.now()  # store the oldest time parsed
        old_af = datetime.datetime(1, 1, 1)  # just some really old date
        for channel in channels:
            try:
                # loop through messages in history (limit 1000 messages per channel)
                async for msg in channel.history(limit=1000):
                    # update oldest
                    oldest = min(oldest, msg.created_at)
                    # add/update data for message author
                    if msg.author in members:
                        try:
                            # use the most recent date
                            data[msg.author] = max(data[msg.author], msg.created_at)
                        except KeyError:
                            data[msg.author] = msg.created_at
            except discord.Forbidden:
                # We do not have permission to read this channel's history
                # await ctx.send("Cannot read channel {0}.".format(channel))
                pass
        # make sure we have data for each member
        for member in members:
            if member not in data:
                # use join date if it's more recent than oldest
                if member.joined_at > oldest:
                    data[member] = member.joined_at
                else:
                    data[member] = old_af
        # sort members with most inactive 1st
        last_week = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        items = [i for i in sorted(data.items(), key=lambda x: x[1]) if i[1] < last_week]
        lowers = []
        output = []

        async def demote(m, dt):
            roles = [r for r in m.roles if r.name not in ['@everyone', 'Nitro Booster']]
            await m.remove_roles(*roles, reason='Inactivity')
            date = dt.date().isoformat()
            return '{0.display_name} demoted (last active {1})'.format(m, date)

        for i in items:
            if i[0].top_role == recruit:
                output.append(await demote(*i))
            elif i[0].top_role <= recruit:
                if i[0].top_role.name not in ['Lone Wolf']:
                    lowers.append(i)
        await split_send(ctx, output)

        async def prompt_kick(m, dt):
            date = dt.date().isoformat()
            msg = 'Should I kick {0.display_name} (#{0.discriminator}), last active {1}?'
            msg = await ctx.send(msg.format(m, date))
            await msg.add_reaction('✅')
            await msg.add_reaction('❌')
            self._kicks.append([msg, m])

        for i in lowers:
            await prompt_kick(*i)

        return

    @commands.command()
    async def roles(self, ctx):
        """List server roles"""
        await ctx.send("\n".join([i.name for i in ctx.guild.roles
                                  if 'everyone' not in i.name]))

    @commands.command()
    async def channel_hist(self, ctx, channel: str = None, n: int = 10):
        """<channel (optional)> shows channel history (past 10 entries)"""
        if channel:
            channel = find_channel(ctx.guild, channel)
        else:
            channel = ctx.channel
        hist = await channel.history(limit=n).flatten()
        msg = ["Item {0:d} {1.id}\n{1.content}".format(i + 1, m)
               for i, m in enumerate(hist)]
        if not msg:
            msg = ["No history available."]
        print(msg)
        await split_send(ctx, msg)

    @commands.command()
    async def member_hist(self, ctx, member: discord.Member = None):
        """<member (optional)> shows member history (past 10 entries)"""
        if member is None:
            member = ctx.author
        hist = await member.history(limit=10).flatten()
        if not hist:
            user = self.bot.get_user(member.id)
            hist = await user.history(limit=10).flatten()
        msg = '\n'.join(["Item {0:d}\n{1.content}".format(i + 1, m)
                         for i, m in enumerate(hist)])
        if not msg:
            msg = "No history available."
        logger.printv(str(hist))
        await ctx.send(msg)

    @commands.command()
    async def bots(self, ctx):
        """Lists server bots"""
        bots = [m for m in ctx.guild.members if m.bot]
        # electro is a bot, so make sure he's included
        electro = ctx.guild.get_member_named('UnknownElectro#1397')
        if electro and electro not in bots:
            bots.insert(0, electro)
        # add other members to bots for fun
        adds = param.rc('add_bots')
        adds = [ctx.guild.get_member_named(i) for i in adds]
        adds = [i for i in adds if i and i not in bots]
        bots += adds
        # construct message
        msg = 'Listing bots for {0.guild}:\n'.format(ctx)
        msg += '\n'.join([str(i + 1) + ') ' + b.display_name for i, b in enumerate(bots)])
        await ctx.send(msg)

    async def emote(self, ctx, emote, n: int = 1, channel: str = None, guild: str = None):
        """emote <n (optional)> <channel (optional)> <server (optional)>
        posts emote"""
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
        n = min(10, n)
        msg = " ".join([emote] * n)
        await channel.send(msg)

    @commands.command()
    async def blob(self, ctx, n: int = 1, channel: str = None, guild: str = None):
        """<n (optional)> <channel (optional)> <server (optional)> posts dancing blob"""
        emote = "<a:blobDance:738431916910444644>"
        await self.emote(ctx, emote, n=n, channel=channel, guild=guild)

    @commands.command()
    async def vibe(self, ctx, n: int = 1, channel: str = None, guild: str = None):
        """<n (optional)> <channel (optional)> <server (optional)> posts vibing cat"""
        emote = "<a:vibe:761582456867520532>"
        await self.emote(ctx, emote, n=n, channel=channel, guild=guild)

    @commands.command()
    async def karen_electro(self, ctx, n: int = 1, channel: str = None, guild: str = None):
        """<n (optional)> <channel (optional)> <server (optional)> posts vibing cat"""
        emote = "<:karen_electro:779088291496460300>"
        await self.emote(ctx, emote, n=n, channel=channel, guild=guild)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for DMs and post them in the bot log channel"""
        if message.author == self.bot.user:
            return
        if type(message.channel) == discord.DMChannel:
            channel = self.bot.find_channel(param.rc('log_channel'))
            msg = 'From: {0.author}\n"{0.content}"'.format(message)
            await channel.send(msg)

    @commands.command()
    async def recruits(self, ctx, role: discord.Role = None):
        """<role (optional)> sorted list of recruit join dates (in UTC)."""
        if role is None:
            members = ctx.guild.members
        else:
            members = role.members
        data = dict()
        for member in members:
            data[member] = member.joined_at
        items = sorted(data.items(), key=lambda x: x[1], reverse=True)
        msg = ['{0.display_name} {1}'.format(i[0], i[1].date().isoformat())
               for i in items]
        await split_send(ctx, msg, style='```')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Parse reaction adds for agreeing to code of conduct and rank them up to
        Recruit"""
        # if reaction is to a kick quarry
        ids = [k[0].id for k in self._kicks]
        if payload.message_id in ids:
            emoji = str(payload.emoji)
            if emoji in ['✅', '❌']:
                guild = await self.bot.fetch_guild(payload.guild_id)
                if await admin_check(author=payload.member, guild=guild):
                    if emoji == '✅':
                        index = ids.index(payload.message_id)
                        msg, member = self._kicks.pop(index)
                        await member.kick(reason='Inactivity')
                        await msg.add_reaction('🔨')
                        return
                    if emoji == '❌':
                        index = ids.index(payload.message_id)
                        msg, member = self._kicks.pop(index)
                        await msg.add_reaction('👌')
                        return
        await self.bot.emoji2role(payload, {'👍': "Wit Challengers"}, message_id=809302963990429757)


def setup(bot):
    """This is required to add this cog to a bot as an extension"""
    bot.add_cog(MainCommands(bot))
