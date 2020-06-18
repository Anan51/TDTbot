import asyncio
import discord
from discord.ext import commands
import datetime
import pytz
import random
import re
from . import param


async def find_channel(guild, name=None):
    if name is None:
        name = param.rc['channel']
    return [i for i in guild.channels if i.name.lower() == name.lower()][0]


async def find_role(guild, name):
    return [i for i in guild.roles if i.name.lower() == name.lower()][0]


def roast_str():
    return random.choice(param.rc['roasts'])


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
        channels = [i for i in ctx.guild.channels if hasattr(i, "history")]
        oldest = datetime.datetime.now()
        old_af = datetime.datetime(1, 1, 1)
        for channel in channels:
            try:
                async for msg in channel.history(limit=1000):
                    oldest = min(oldest, msg.created_at)
                    if msg.author in members:
                        try:
                            data[msg.author] = max(data[msg.author], msg.created_at)
                        except KeyError:
                            data[msg.author] = msg.created_at
            except discord.Forbidden:
                # await ctx.send("Cannot read channel {0}.".format(channel))
                pass
        for member in members:
            if member not in data:
                if member.joined_at > oldest:
                    data[member] = member.joined_at
                else:
                    data[member] = old_af
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
        """<member (optional)> shows member history"""
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
        """<member (optional)> shows member history"""
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
        print(str(hist))
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
        """<channel (optional)> <server (optional)> NO U"""
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

    async def cog_check(self, ctx):
        a = ctx.author
        if a.roles[0].name in ['Admin', 'Devoted']:
            return True
        if await self.bot.is_owner(a):
            return True
        if ctx.guild.owner == a:
            return True
        return False

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
            channel = await find_channel(guild, channel)
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


class Alerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.get_channel('Debugging')
        roles = [await find_role(member.guild, i) for i in ["Admin", "Devoted"]]
        roles = " ".join([i.mention for i in roles if hasattr(i, 'mention')])
        if channel is not None:
            await channel.send(roles + ' new member {0.name} joined.'.format(member))


class Roast(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._nemeses = param.rc('nemeses')
        self._last_roast = None

    @commands.command()
    async def roast(self, ctx, channel: str = None, guild: str = None):
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
            channel = await find_channel(guild, channel)
        else:
            channel = ctx.channel
        self._last_roast = await channel.fetch_message(channel.last_message_id)
        await channel.send(roast_str())

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content.startswith(self.bot.command_prefix):
            return
        if message.author == self.bot.user:
            return
        triggers = ['<:lenny:333101455856762890> <:OGTriggered:433210982647595019>']
        if (re.match('^[rR]+[Ee][Ee]+$', message.content.strip())
                or message.content.strip() in triggers):
            await message.channel.send(roast_str())
            self._last_roast = message
            return
        old = self._last_roast
        if old:
            if message.author == old.author and message.channel == old.channel:
                if (message.created_at - old.created_at).total_seconds() < 60:
                    if message.content.strip() in ['omg', 'bruh']:
                        await message.channel.send(roast_str())
                        self._last_roast = None
                        return
                    self._last_roast = None
        # if the nemesis of this bot posts a non command message then roast them with
        # 1/20 probability
        try:
            if message.author.name in self._nemeses:
                if not random.randrange(20):
                    await message.channel.send(roast_str())
                    self._last_roast = message.author
        except TypeError:
            pass
        return


def parse_event(message):
    tz = pytz.timezone('America/Los_Angeles')
    lines = [i.strip() for i in message.content.split('\n')]
    if len(lines) < 5:
        return 'len < 5'
    out = dict(message=message)
    out['name'] = lines[0]
    keys = ['who', 'what', 'when']
    for line in lines[1:4]:
        try:
            key, value = [i.strip() for i in line.split(':')]
        except IndexError:
            return 'key, value error'
        if key.lower() not in keys:
            return 'kew without lowe'
        out[key.lower()] = value
    for key in keys:
        if key not in out:
            return 'key not in out'
    out['enroll'] = '\n'.join(lines[4:])
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday',
                    'sunday']
    day = None
    for d in days_of_week:
        if d in out['when'].lower():
            day = d
            break
    if not day:
        return 'no day'
    today = datetime.datetime.now(tz=tz).date()
    i = 0
    while (today + datetime.timedelta(days=i)).weekday() != days_of_week.index(day):
        i += 1
    day = today + datetime.timedelta(days=i)
    t = None
    # parse date/time
    if ':' in out['when']:
        try:
            time = re.findall('\d+:\d+[ ]?[ap]m', out['when'].lower())[0]
            fmt = '%I:%M %p' if ' ' in time else '%I:%M%p'
            t = datetime.datetime.strptime(time, fmt)
        except IndexError:
            t = datetime.datetime.strptime(re.findall('\d', out['when'].lower())[0],
                                           '%H:%M')
            if 'night' in out['when'].lower() and t.hour < 12:
                t += datetime.timedelta(hours=12)
            elif t.hour < 8 and 'morning' not in out['when'].lower():
                t += datetime.timedelta(hours=12)
    else:
        try:
            time = re.findall('\d+[ ]?[ap]m', out['when'].lower())[0]
            fmt = '%I %p' if ' ' in time else '%I%p'
            t = datetime.datetime.strptime(time, fmt)
        except IndexError:
            t = datetime.datetime.strptime(re.findall('\d', out['when'].lower())[0], '%H')
            if 'night' in out['when'].lower() and t.hour < 12:
                t += datetime.timedelta(hours=12)
            elif t.hour < 8 and 'morning' not in out['when'].lower():
                t += datetime.timedelta(hours=12)
    if not t:
        return 'no t'
    out['datetime'] = datetime.datetime.combine(day, t.time())
    out['dt_str'] = out['datetime'].strftime('%X %A %x')
    msg = 'Event "{name}" registered for {dt_str}'.format(**out)
    print(out)
    return msg


class Events(commands.Cog):
    def __init__(self, bot, channel=None):
        self.bot = bot
        if channel is None:
            channel = param.rc('event_channel')
        self.channel = channel

    def is_event_channel(self, channel):
        if type(self.channel) == int:
            return channel.id == self.channel
        if hasattr(self.channel, "lower"):
            print(channel.name, self.channel)
            return channel.name == self.channel
        return channel == self.channel

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.content.startswith(self.bot.command_prefix):
            return
        if self.is_event_channel(message.channel):
            event = parse_event(message)
            if event:
                await message.channel.send(event)

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
        self.add_cog(Roast(self))
        # self.add_cog(Events(self))

        @self.event
        async def on_ready():
            msg = 'We have logged in as {0.user}, running {1.__version__}'
            print(msg.format(self, discord))
            activity = discord.Activity(name='UnknownElectro be a bot',
                                        type=discord.ActivityType.listening)
            await self.change_presence(activity=activity)

        @self.event
        async def on_command_error(ctx, error):
            await ctx.send(str(error))

    async def bot_check(self, ctx):
        if ctx.channel.name in param.rc('ignore_list'):
            return False
        return True
