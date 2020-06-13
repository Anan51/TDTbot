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
        msg = '\n'.join([m[0] + ' ' + m[1].isoformat() for m in msg])
        # msg = '\n'.join([i.display_name + ' ' + data[i].isoformat for i in data])
        # channel = await find_channel(ctx.guild)
        await ctx.send(msg)

    @commands.command()
    async def roles(self, ctx):
        """List server roles"""
        await ctx.send("\n".join([i.name for i in ctx.guild.roles
                                  if 'everyone' not in i.name]))

    @commands.command()
    async def RuntimeError(self, ctx):
        """Raise a runtime error (because why not)"""
        raise RuntimeError("Per user request")


class Alerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.get_channel('test')
        if channel is not None:
            await channel.send('Welcome {0.mention}.'.format(member))


_bot = commands.Bot(command_prefix=param.rc['cmd_prefix'])
_bot.add_cog(MainCommands(_bot))
_bot.add_cog(Alerts(_bot))


@_bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(_bot))


def run(token=None):
    if token is None:
        token = param.rc['token']
    if not token:
        raise ValueError('No token provided.')
    _bot.run(token)

