import datetime
import discord
from discord.ext import commands
import humanize
from ..helpers import *
from .. import git_manage


class Debugging(commands.Cog):
    """Cog designed for debugging the bot"""
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Don't allow everyone to access this cog"""
        a = ctx.author
        if a.roles[0].name in ['Admin', 'Devoted']:
            return True
        if await self.bot.is_owner(a):
            return True
        if ctx.guild.owner == a:
            return True
        return False

    @commands.command(hidden=True)
    async def RuntimeError(self, ctx):
        """Raise a runtime error (because why not)"""
        raise RuntimeError("Per user request")

    @commands.command(hidden=True)
    async def flush(self, ctx, n: int = 10):
        """<n=10 (optional)> flushes stdout with n newlines"""
        print('\n' * n)

    @commands.command(hidden=True)
    async def reboot(self, ctx):
        """Reboots this bot"""
        await ctx.send("Ok. I will reboot now.")
        print('\nRebooting\n\n\n\n')
        # This exits the bot loop, allowing __main__ loop to take over
        await self.bot.loop.run_until_complete(self.bot.logout())

    @commands.command(hidden=True)
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

    @commands.command(hidden=True)
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

    @commands.command(hidden=True)
    async def git_pull(self, ctx):
        """Do a git pull on own code"""
        git_manage.update()

    @commands.command(hidden=True)
    async def reload_cogs(self, ctx, option=None):
        """Reloads all cogs that were added as extensions"""
        if option == 'pull':
            await self.git_pull(ctx)
        msg = 'Reloading ' + ', '.join([i.split('.')[-1] for i in self.bot.extensions])
        for i in self.bot.extensions:
            self.bot.reload_extension(i)
        await ctx.send(msg.rstrip(', '))

    @commands.command(hidden=True)
    async def print(self, ctx, *args):
        """Print text following command to terminal. This is useful for emojis."""
        print(' '.join(args))

    @commands.command(hidden=True)
    async def param(self, ctx, *args):
        """Print param to discord chat."""
        from .. import param
        if param.rc:
            msg = '\n'.join(["{:}: {:}".format(*[i, param.rc[i]]) for i in param.rc
                             if i not in ['roasts', 'token']])
            await ctx.send('```' + msg + '```')
        else:
            await ctx.send("Param is empty.")

    @commands.command(hidden=True)
    async def git_log(self, ctx, *args):
        """Print git log to discord chat."""
        master = git_manage.own_repo.heads.master
        now = datetime.datetime.now()
        last_week = now - datetime.timedelta(days=7)
        # only print items from the last week
        items = [i for i in master.log()[::-1]
                 if datetime.datetime.fromtimestamp(i.time[0]) > last_week]

        def dt(i):
            """Format timestamp to human readable string"""
            t0 = datetime.datetime.fromtimestamp(i.time[0])
            return humanize.naturaltime(now - t0)

        fmt = "{:} {:} <{:}> [{:}]"
        msg = [fmt.format(dt(i), i.message, i.actor.name, i.newhexsha[:7]) for i in items]
        await ctx.send('```' + '\n'.join(msg) + '```')


def setup(bot):
    bot.add_cog(Debugging(bot))
