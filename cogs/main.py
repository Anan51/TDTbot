import datetime
import discord
from discord.ext import commands
import logging
from .. import param
from ..helpers import *


logger = logging.getLogger('discord')


class MainCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

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
        msg = '\n'.join(['{0.display_name} {1}'.format(i[0], i[1].date().isoformat())
                         for i in items])
        await ctx.send('```' + msg + '```')

    @commands.command()
    async def roles(self, ctx):
        """List server roles"""
        await ctx.send("\n".join([i.name for i in ctx.guild.roles
                                  if 'everyone' not in i.name]))

    @commands.command()
    async def channel_hist(self, ctx, channel: discord.ChannelType = None):
        """<channel (optional)> shows channel history (past 10 entries)"""
        if channel is None:
            channel = ctx.channel
        hist = await channel.history(limit=10).flatten()
        msg = '\n'.join(["Item {0:d}\n{1.content}".format(i + 1, m)
                         for i, m in enumerate(hist)])
        if not msg:
            msg = "No history available."
        await ctx.send(msg)

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


def setup(bot):
    """This is required to add this cog to a bot as an extension"""
    bot.add_cog(MainCommands(bot))
