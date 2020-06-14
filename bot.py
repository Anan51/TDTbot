import asyncio
import discord
from discord.ext import commands
from . import param


async def last_active(member):
    messages = await member.history(limit=1).flatten()
    if not messages:
        return member.joined_at
    return messages[0].created_at


async def find_channel(guild, name=None):
    if name is None:
        name = param.rc['channel']
    return [i for i in guild.channels if i.name.lower() == name.lower()][0]


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
        if role is None:
            try:
                role = [r for r in ctx.guild.roles if r.name.lower() == 'community'][0]
            except IndexError:
                pass
        if not role:
            members = ctx.guild.members
        else:
            members = role.members
        data = {m.display_name: await last_active(m) for m in members}
        msg = sorted(data.items(), key=lambda x: x[1])
        msg = '\n'.join([m[0] + ' ' + m[1].date().isoformat() for m in msg])
        # msg = '\n'.join([i.display_name + ' ' + data[i].isoformat for i in data])
        # channel = await find_channel(ctx.guild)
        await ctx.send(msg)

    @commands.command()
    async def roles(self, ctx):
        """List server roles"""
        await ctx.send("\n".join([i.name for i in ctx.guild.roles
                                  if 'everyone' not in i.name]))

    @commands.command()
    async def hist(self, ctx, member: discord.Member = None):
        """<member (optional)> shows member history"""
        if member is None:
            member = ctx.author
        hist = await member.history(limit=100).flatten()
        msg = '\n'.join([str(i) for i in hist])
        if self.bot.read_message_history:
            await ctx.send("Recovering history:")
        else:
            await ctx.send("I do not have permission to read the history")
            return
        if not msg:
            msg = "No history available."
        await ctx.send(msg)

    @commands.command()
    async def bots(self, ctx):
        """Lists server bots"""
        bots = [m for m in ctx.guild.members if m.bot]
        electro = ctx.guild.get_member_named('UnknownElectro#1397')
        if electro:
            bots.insert(0, electro)
        msg = 'Listing bots for {0.guild}:\n'.format(ctx)
        msg += '\n'.join([str(i + 1) + ') ' + b.display_name for i, b in enumerate(bots)])
        await ctx.send(msg)

    @commands.command()
    async def nou(self, ctx, channel: str = None, guild: str = None):
        if guild is None:
            guild = ctx.guild
        else:
            try:
                guild = [i for i in self.bot.guilds if i.name == guild][0]
            except IndexError:
                ctx.send("NO U (need to type a reasonable server name)")
                return
        if channel:
            channel = await find_channel(guild, channel)
        else:
            channel = ctx.channel
        await channel.send("NO U")


class Debugging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def RuntimeError(self, ctx):
        """Raise a runtime error (because why not)"""
        raise RuntimeError("Per user request")

    @commands.command()
    async def flush(self, ctx, n: int = 10):
        """<n=10 (optional)> flushes stdout with n newlines"""
        print('\n' * n)

    @commands.command()
    async def reboot(self, ctx):
        """Reboots this bot"""
        await ctx.send("Ok. I will reboot now.")
        print('\nRebooting\n\n\n\n')
        await self.bot.loop.run_until_complete(self.bot.logout())


class Alerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.get_channel('Debugging')
        if channel is not None:
            await channel.send('Welcome {0.mention}.'.format(member))


class MainBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        if 'command_prefix' not in kwargs:
            kwargs['command_prefix'] = param.rc['cmd_prefix']
        if 'loop' not in kwargs:
            kwargs['loop'] = asyncio.new_event_loop()
        super().__init__(*args, **kwargs)
        self.add_cog(MainCommands(self))
        self.add_cog(Alerts(self))
        self.add_cog(Debugging(self))

        @self.event
        async def on_ready():
            print('We have logged in as {0.user}'.format(self))
