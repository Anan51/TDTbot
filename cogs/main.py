import datetime
import discord
from discord.ext import commands
import logging
from .. import param, users
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
    async def roles(self, ctx):
        """List server roles"""
        await ctx.send("\n".join([i.name for i in ctx.guild.roles
                                  if 'everyone' not in i.name]))

    @commands.command()
    async def bots(self, ctx):
        """Lists server bots"""
        bots = [m for m in ctx.guild.members if m.bot]
        # electro is a bot, so make sure he's included
        electro = await self.bot.get_or_fetch_user(users.electro, ctx.guild)
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

    async def emote(self, ctx, emote, n: int = 1, channel: discord.TextChannel = None,
                    guild: str = None):
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
    async def blob(self, ctx, n: int = 1, channel: discord.TextChannel = None,
                   guild: str = None):
        """<n (optional)> <channel (optional)> <server (optional)> posts dancing blob"""
        emote = "<a:blobDance:738431916910444644>"
        await self.emote(ctx, emote, n=n, channel=channel, guild=guild)

    @commands.command()
    async def vibe(self, ctx, n: int = 1, channel: discord.TextChannel = None, guild: str = None):
        """<n (optional)> <channel (optional)> <server (optional)> posts vibing cat"""
        emote = "<a:vibe:761582456867520532>"
        await self.emote(ctx, emote, n=n, channel=channel, guild=guild)

    @commands.command()
    async def karen_electro(self, ctx, n: int = 1, channel: discord.TextChannel = None, guild: str = None):
        """<n (optional)> <channel (optional)> <server (optional)> posts vibing cat"""
        emote = "<:karen_electro:779088291496460300>"
        await self.emote(ctx, emote, n=n, channel=channel, guild=guild)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Template for message listeners"""
        # ignore messages from this bot
        if message.author == self.bot.user:
            return
        # ignore commands
        try:
            if message.content.startswith(self.bot.command_prefix):
                return
        except TypeError:
            for prefix in self.bot.command_prefix:
                if message.content.startswith(prefix):
                    return
        # Do something with the message below
        return

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
        await self.bot.emoji2role(payload, {'👍': "Wit Challengers"}, message_id=809302963990429757)
        await self.bot.emoji2role(payload, {'🏆': "Tourney Challengers"}, message_id=822744897505067018)
        _roles = {i: i for i in ['alpha', 'beta', 'gamma', 'omega']}
        await self.bot.emoji2role(payload, _roles, message_id=943278519394402314)

    @commands.command()
    @commands.check(admin_check)
    async def add_roles(self, ctx, role: discord.Role, emote: str = None,
                        msg_id: int = None, channel: discord.abc.Messageable = None):
        """<role> <emote (optional)> <message id (optional)> <channel (optional)>
        For all members who have already reacted to given message with given emote,
        assign them the given role.

        Can be used as a reply to a message, in this case:
        <message id> defaults to the message that's being replied to.
        <emote> defaults to the emote with the most reactions.
        <channel> defaults to the channel where this command was entered."""

        ref = ctx.message.reference
        if channel is None:
            channel = ctx.channel
        msg = None
        if msg_id is not None:
            msg = await channel.fetch_message(msg_id)
        if msg is None and msg_id is None and ref:
            if hasattr(ref, 'resolved'):
                msg = ref.resolved
            else:
                channel = self.bot.find_channel(ref.channel_id)
                if channel is None:
                    channel = await self.bot.fetch_channel(ref.channel_id)
                if channel is None:
                    msg = ref
                else:
                    msg = await channel.fetch_message(ref.message_id)
        if not msg:
            raise ValueError("Cannot identify message.")
        rxns = sorted([rxn for rxn in msg.reactions], key=lambda x: x.count, reverse=True)
        try:
            if emote is not None:
                rxns = [rxn for rxn in rxns if emotes_equal(emote, rxn.emoji)]
            else:
                emote = rxns[0].emoji
            users = await rxns[0].users().flatten()
        except IndexError:
            users = []
        n = 0
        errors = []
        for user in users:
            try:
                await user.add_roles(role)
                n += 1
            except Exception as e:
                err = "Cannot add {} role to user {} with error {}."
                errors.append(err.format(role, user, e))
        if errors:
            await split_send(ctx, errors, style='```')
        out = 'Added role {} to {} player{} who reacted with {} to message {}.'
        out.format(role, n, 's' if n > 1 else 0, emote, msg.id)
        try:
            msg.reply(out, mention_author=False)
        except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument):
            ctx.send(out)

    @commands.command()
    async def source(self, ctx):
        """Source code for this bot."""
        await ctx.send('My source code is available at https://github.com/TDTcode/TDTbot')


def setup(bot):
    """This is required to add this cog to a bot as an extension"""
    bot.add_cog(MainCommands(bot))
