import datetime
import discord
from discord.ext import commands
import humanize
import logging
import pytz
from ..helpers import *
from ..async_helpers import admin_check, split_send
from .. import git_manage


logger = logging.getLogger('discord.' + __name__)


class Debugging(commands.Cog):
    """Cog designed for debugging the bot"""
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Don't allow everyone to access this cog"""
        return await admin_check(ctx)

    @commands.command()
    async def RuntimeError(self, ctx):
        """Raise a runtime error (because why not)"""
        raise RuntimeError("Per user request")

    @commands.command()
    async def flush(self, ctx, n: int = 10):
        """<n=10 (optional)> flushes stdout with n newlines"""
        logger.printv('\n' * n)

    @commands.command()
    async def reboot(self, ctx):
        """Reboots this bot"""
        await ctx.send("Ok. I will reboot now.")
        logger.printv('\nRebooting\n\n\n\n')
        # This exits the bot loop, allowing __main__ loop to take over
        await self.bot.loop.run_until_complete(await self.bot.logout())

    @commands.command()
    async def channel_id(self, ctx, channel: str = None, guild: str = None):
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
        await ctx.send('Channel "{0.name}" has id {0.id}.'.format(channel))

    @commands.command()
    async def member_id(self, ctx, member: str = None, guild: str = None):
        """<channel (optional)> <server (optional)> sends random roast message"""
        if guild is None:
            guild = ctx.guild
        else:
            try:
                guild = [i for i in self.bot.guilds if i.name == guild][0]
            except IndexError:
                ctx.send('ERROR: server "{0}" not found.'.format(guild))
                return
        if member:
            member = guild.get_member_named(member)
        else:
            member = ctx.author
        await ctx.send('{0.name} has id {0.id}.'.format(member))

    @commands.command()
    async def git_pull(self, ctx):
        """Do a git pull on own code"""
        git_manage.update()
        await ctx.send("Pulled own code")

    @commands.command()
    async def reload_cogs(self, ctx, option=None):
        """Reloads all cogs that were added as extensions"""
        if option == 'pull':
            await self.git_pull(ctx)
        msg = 'Reloading ' + ', '.join([i.split('.')[-1] for i in self.bot.extensions])
        for i in self.bot.extensions:
            self.bot.reload_extension(i)
        await ctx.send(msg.rstrip(', '))

    @commands.command()
    async def print(self, ctx, *args):
        """Print text following command to terminal. This is useful for emojis."""
        logger.printv(' '.join(args))

    @commands.command()
    async def param(self, ctx, *args):
        """Print param to discord chat."""
        from .. import param
        if param.rc:
            msg = '\n'.join(["{:}: {:}".format(*[i, param.rc[i]]) for i in param.rc
                             if i not in ['roasts', 'token']])
            await ctx.send('```' + msg + '```')
        else:
            await ctx.send("Param is empty.")

    @commands.command()
    async def git_log(self, ctx, *args):
        """Print git log to discord chat."""
        now = pytz.utc.localize(datetime.datetime.utcnow())
        last_week = now - datetime.timedelta(days=7)
        # only print items from the last week
        items = [i for i in git_manage.own_repo.iter_commits()
                 if i.committed_datetime > last_week]

        def dt(i):
            """Format timestamp to human readable string"""
            return humanize.naturaltime(now - i.committed_datetime)

        fmt = "{:}: {:} <{:}> [{:}]"
        msg = [fmt.format(dt(i), i.message.strip(), i.author.name, i.hexsha[:7])
               for i in items]
        await ctx.send('```' + '\n'.join(msg) + '```')

    @commands.group()
    async def git(self, ctx):
        """Base function for git sub commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid git command passed...')

    @git.command()
    async def pull(self, ctx):
        """Alias for git_pull"""
        await self.git_pull(ctx)

    @git.command()
    async def log(self, ctx):
        """Alias for git_log"""
        await self.git_log(ctx)

    @commands.command()
    async def reload_extension(self, name):
        self.bot.reload_extension(name)

    @commands.command()
    async def speak(self, ctx, message, channel: str = None, guild: str = None):
        """Speak as the bot"""
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
        await channel.send(message)

    @commands.command()
    async def print_roles(self, ctx, member: str = None, guild: str = None):
        """<channel (optional)> <server (optional)> sends random roast message"""
        if guild is None:
            guild = ctx.guild
        else:
            try:
                guild = [i for i in self.bot.guilds if i.name == guild][0]
            except IndexError:
                ctx.send('ERROR: server "{0}" not found.'.format(guild))
                return
        if member:
            member = guild.get_member_named(member)
        else:
            member = ctx.author
        print(member.roles)

    @commands.command()
    async def id_this(self, ctx):
        ref = ctx.message.reference
        msg = ctx.message
        if ref:
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
        if hasattr(msg, 'id'):
            txt = ['message id: ' + str(msg.id),
                   'channel id: ' + str(msg.channel.id),
                   'guild id: ' + str(msg.guild.id)]
        else:
            txt = ['{}: {}'.format(i.replace('_', ' '), getattr(msg, i, 'unknown'))
                   for i in ['message_id', 'channel_id', 'guild_id']]
        if hasattr(msg, 'author'):
            a = msg.author
            txt.append('author: {}'.format(a.display_name))
            txt.append('author id: {0}'.format(a.id))
        await split_send(ctx, txt)

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
        await split_send(ctx, msg)

    @commands.command()
    @commands.check(admin_check)
    async def clear_rxn(self, ctx, emote: str, msg_id: int = None,
                        channel: discord.abc.Messageable = None):
        """<emote> <message id (optional)> <channel (optional)>
        Clear all of the specified reaction for the message

        Can be used as a reply to a message, in this case:
        <message id> defaults to the message that's being replied to.
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
        rxns = [rxn for rxn in msg.reactions if emotes_equal(emote, rxn.emoji)]
        if rxns:
            await rxns[0].clear()


def setup(bot):
    bot.add_cog(Debugging(bot))
