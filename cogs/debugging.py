import datetime
import discord
from discord.ext import commands
import humanize
import logging
import pytz
from ..helpers import *
from ..async_helpers import admin_check
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


def setup(bot):
    bot.add_cog(Debugging(bot))
