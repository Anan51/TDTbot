import discord
from discord.ext import commands
from . import param


async def last_active(member):
    messages = await member.history(limit=1).flatten()
    if not messages:
        return member.joined_at
    return messages[0].created_at


class MainCommands(commands.Cog):
    def __init__(self, bot, channel=None):
        self.bot = bot
        self._last_member = None
        if channel is None:
            channel = param.rc['channel']
        if hasattr(channel, 'lower'):
            channel = channel.lower()
            channel = [i for i in bot.guild.channels if i.name.lower() == channel][0]
        self._channel = channel

    @commands.command()
    async def guild(self, ctx):
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
        if role is None:
            role = [r for r in ctx.guild.roles if r.name.lower == 'community'][0]
        if not role:
            members = ctx.guild.members
        else:
            members = role.members
        data = {m: last_active(m) for m in members}
        msg = sorted(data.items(), key=lambda x: x[1], reverse=True)
        msg = '\n'.join([m[0].name + ' ' + m[1].isoformat for m in msg])
        await self._channel.send(msg)


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

