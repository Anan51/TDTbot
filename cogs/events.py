import asyncio
import discord
from discord.ext import commands
import datetime
import pytz
import re
from .. import param
from ..helpers import *


async def wait_until(dt):
    # sleep until the specified datetime
    while True:
        now = datetime.datetime.now()
        remaining = (dt - now).total_seconds()
        if remaining < 86400:
            break
        # asyncio.sleep doesn't like long sleeps, so don't sleep more
        # than a day at a time
        await asyncio.sleep(86400)
    await asyncio.sleep(remaining)


class _Event(dict):
    def __init__(self, message, cog, log_channel=None):
        super().__init__()
        self.cog = cog
        self._pending_alerts = True
        if log_channel is None:
            log_channel = param.rc('log_channel')
        self.log_channel = self.cog.bot.find_channel(log_channel)
        tz = pytz.timezone('America/Los_Angeles')
        lines = [i.strip() for i in message.content.split('\n')]
        if len(lines) < 5:
            return
        out = dict(id=message.id)
        self._message_channel = message.channel
        out['name'] = lines[0]
        keys = ['who', 'what', 'when']
        for line in lines[1:4]:
            try:
                key, value = [i.strip() for i in line.split(':')]
            except IndexError:
                return
            if key.lower() not in keys:
                return
            out[key.lower()] = value
        for key in keys:
            if key not in out:
                return
        out['enroll'] = '\n'.join(lines[4:])
        days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                        'saturday', 'sunday']
        day = None
        for d in days_of_week:
            if d in out['when'].lower():
                day = d
                break
        if not day:
            return
        today = datetime.datetime.now(tz=tz).date()
        i = 0
        while (today + datetime.timedelta(days=i)).weekday() != days_of_week.index(day):
            i += 1
        day = today + datetime.timedelta(days=i)
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
                t = datetime.datetime.strptime(re.findall('\d', out['when'].lower())[0],
                                               '%H')
                if 'night' in out['when'].lower() and t.hour < 12:
                    t += datetime.timedelta(hours=12)
                elif t.hour < 8 and 'morning' not in out['when'].lower():
                    t += datetime.timedelta(hours=12)
        if not t:
            return
        out['datetime'] = datetime.datetime.combine(day, t.time())
        self.update(out)
        return

    async def message(self):
        return await self._message_channel.fetch_message(self['id'])

    @property
    def dt_str(self):
        return self['datetime'].strftime('%X %A %x')

    @property
    def name(self):
        return self['name']

    @property
    def log_message(self):
        return 'Event "{0.name}" registered for {0.dt_str}'.format(self)

    @property
    def id(self):
        return self['id']

    async def record_log(self, log_channel=None):
        after = self['datetime'] - datetime.timedelta(days=6, hours=23)
        log = self.log_message
        if log_channel is None:
            log_channel = self.log_channel
        async for msg in log_channel.history(limit=200, after=after):
            if msg.content == log:
                return
        await self.log_channel.send(log)

    def past(self):
        return self['datetime'] < datetime.datetime.now()

    async def attendees(self):
        msg = await self.message()
        out = []
        for rxn in msg.reactions:
            out.extend(await rxn.users().flatten())
        return set(out)

    async def alert(self, dt_min=None, channel=None, suffix=None, wait=True):
        if channel is None:
            channel = getattr(self.cog, 'channel', param.rc('event_channel'))
        channel = self.cog.bot.find_channel(channel)
        if suffix is None:
            if dt_min is None:
                suffix = " your event is approaching."
            elif dt_min == 0:
                suffix = " your event is starting now."
            elif dt_min % 60 == 0:
                suffix = " your event is starting in {:d} hour(s).".format(dt_min // 60)
            else:
                suffix = " your event is starting in {:d} minute(s).".format(dt_min // 60)
        if wait:
            await wait_until(self['datetime'] - datetime.timedelta(minutes=dt_min))
        msg = ' '.join([i.mention for i in await self.attendees()]) + suffix
        await channel.send(msg)

    def set_alerts(self, dts=None, channel=None):
        if self._pending_alerts:
            return
        if dts is None:
            dts = param.rc('event_reminders')
        for dt in dts:
            self.cog.bot.loop.create_task(self.alert(dt, channel=channel))
        self._pending_alerts = True

    async def log_and_alert(self, dts=None, event_chanel=None, log_channel=None):
        await self.record_log(log_channel=log_channel)
        self.set_alerts(dts=dts, channel=event_chanel)


class Events(commands.Cog):
    def __init__(self, bot, channel=None, log_channel=None):
        self.bot = bot
        if channel is None:
            channel = param.rc('event_channel')
        self._channel = channel
        if log_channel is None:
            log_channel = param.rc('log_channel')
        self._log_channel = log_channel
        self._events = []
        self._hist_checked = False

    @property
    def channel(self):
        if hasattr(self._channel, 'id'):
            return self._channel
        channel = self.bot.find_channel(self._channel)
        if channel:
            self._channel = channel
            return channel

    @property
    def log_channel(self):
        if hasattr(self._log_channel, 'id'):
            return self._log_channel
        channel = self.bot.find_channel(self._log_channel)
        if channel:
            self._log_channel = channel
            return channel

    def is_event_channel(self, channel):
        if type(self.channel) == int:
            return channel.id == self.channel
        if hasattr(self.channel, "lower"):
            return channel.name == self.channel
        return channel == self.channel

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if not self._hist_checked:
            await self.check_history()
        if message.content.startswith(self.bot.command_prefix):
            return
        if self.is_event_channel(message.channel):
            event = _Event(message, self)
            if event:
                if event not in self._events:
                    self._events.append(event)
                    await event.log_and_alert(event_chanel=self.channel)

    async def check_history(self, channel=None):
        if channel is None:
            channel = self.channel
        after = datetime.datetime.now() - datetime.timedelta(days=6, hours=23)
        async for i in channel.history(after=after, limit=200):
            event = _Event(i, self)
            if event:
                if event not in self._events:
                    self._events.append(event)
                    await event.log_and_alert(event_chanel=channel)
        await self.log_channel.send('History parsed.')
        self._hist_checked = True

    @commands.group()
    async def events(self, ctx):
        """<"attendees"> Lists events and optionally attendees."""
        if ctx.invoked_subcommand is None:
            msg = '{0}) {1.log_message}'
            msg = '\n'.join([msg.format(i + 1, e) for i, e in enumerate(self._events)])
            if msg:
                await ctx.send(msg)
            else:
                ctx.send('No events.')

    @events.command()
    async def attendees(self, ctx):
        msg = []
        fmt = '{0}) {1.name}: {2}'
        for i, e in enumerate(self._events):
            message = await e.message()
            print(e.name, message.reactions)
            users = [j.display_name for j in await e.attendees()]
            msg.append(fmt.format(i + 1, e, ', '.join(users)))
        msg = '\n'.join(msg)
        if msg:
            await ctx.send(msg)
        else:
            await ctx.send('No events.')


def setup(bot):
    bot.add_cog(Events(bot))
