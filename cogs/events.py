import asyncio
import discord
from discord.ext import commands
import datetime
import logging
import pytz
import random
import re
import traceback
from .. import param
from ..helpers import *


logger = logging.getLogger('discord.' + __name__)


async def wait_until(dt):
    """sleep until the specified datetime (assumes UTC)"""
    while True:
        now = datetime.datetime.utcnow()
        remaining = (dt - now).total_seconds()
        if remaining < 86400:
            break
        # asyncio.sleep doesn't like long sleeps, so don't sleep more than a day at a time
        await asyncio.sleep(86400)
    await asyncio.sleep(remaining)


class _Event(dict):
    """A class to contain event info (dict subclass)."""
    def __init__(self, message, cog, log_channel=None, from_hist=False):
        super().__init__()
        # start parsing message for event info
        lines = [i.strip() for i in message.content.split('\n')]
        if len(lines) < 5:
            return
        out = dict()
        out['name'] = lines[0]
        keys = ['who', 'what', 'when']  # check for and get these
        for line in lines[1:4]:
            try:
                tmp = [i.strip() for i in line.split(':')]
                key = tmp[0]
                value = " ".join(tmp[1:])
            except (IndexError, ValueError):
                logger.warning('Missing ":" on message lines.')
                return
            if key.lower() not in keys:
                logger.warning('Unknown key "{:}"'.format(key))
                return
            out[key.lower()] = value
        for key in keys:
            if key not in out:
                logger.warning('Missing key "{:}"'.format(key))
                return
        # text saying how to enroll in event
        out['enroll'] = '\n'.join(lines[4:])
        # parse day of week
        days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                        'saturday', 'sunday']
        day = None
        for d in days_of_week:
            if d in out['when'].lower():
                day = d
                break
        if not day:
            logger.warning("Can't parse day")
            return
        # We only get this far if we have a valid event, so set attributes now
        self.cog = cog
        self._pending_alerts = False
        self.from_hist = from_hist
        if log_channel is None:
            log_channel = param.rc('log_channel')
        self.log_channel = self.cog.bot.find_channel(log_channel)
        tz = pytz.timezone(param.rc('timezone'))
        self.tz = tz
        out['id'] = message.id
        self._message_channel = message.channel
        # Attributes finished now deal with timezone crap
        now = datetime.datetime.now().astimezone(tz).replace(tzinfo=None)
        today = now.date()  # today in server timezone
        i = 0
        # parse day of week into datetime and assume it's the next day with given name
        while (today + datetime.timedelta(days=i)).weekday() != days_of_week.index(day):
            i += 1
        day = today + datetime.timedelta(days=i)
        # parse time text
        if ':' in out['when']:
            try:
                time = re.findall('\d+:\d+[ ]?[ap]m', out['when'].lower())[0]
                fmt = '%I:%M %p' if ' ' in time else '%I:%M%p'
                t = datetime.datetime.strptime(time, fmt)
            except IndexError:
                # if am/pm not provided
                t = datetime.datetime.strptime(re.findall('\d', out['when'].lower())[0],
                                               '%H:%M')
                if 'night' in out['when'].lower() and t.hour < 12:
                    t += datetime.timedelta(hours=12)
                elif t.hour < 8 and 'morning' not in out['when'].lower():
                    t += datetime.timedelta(hours=12)
        # no ":" in text so no hour/minute separator
        else:
            try:
                time = re.findall('\d+[ ]?[ap]m', out['when'].lower())[0]
                fmt = '%I %p' if ' ' in time else '%I%p'
                t = datetime.datetime.strptime(time, fmt)
            except IndexError:
                # if am/pm not provided
                t = datetime.datetime.strptime(re.findall('\d', out['when'].lower())[0],
                                               '%H')
                if 'night' in out['when'].lower() and t.hour < 12:
                    t += datetime.timedelta(hours=12)
                elif t.hour < 8 and 'morning' not in out['when'].lower():
                    t += datetime.timedelta(hours=12)
        if not t:
            logger.warning('Invalid time')
            return
        # make sure datetime is specified with server timezone
        dt = tz.localize(datetime.datetime.combine(day, t.time()))
        # convert it to UTC and strip timezone info (required by external libs)
        out['datetime'] = dt.astimezone(pytz.utc).replace(tzinfo=None)
        # put the contents of out into self
        self.update(out)
        return

    async def message(self):
        """Fetch and return the message associated with this event"""
        # we fetch this every usage to update the reactions
        return await self._message_channel.fetch_message(self['id'])

    @property
    def dt_str(self):
        """Datetime string for this event"""
        # assign UTC timezone to datetime object
        dt = pytz.utc.localize(self['datetime'])
        # convert to server timezone
        return dt.astimezone(self.tz).strftime('%X %A %x')

    @property
    def name(self):
        """Name of event"""
        return self['name']

    @property
    def log_message(self):
        """Return the string we want to send to the log when registering this event"""
        return 'Event "{0.name}" registered for {0.dt_str}'.format(self)

    @property
    def id(self):
        """Message id"""
        return self['id']

    async def record_log(self, log_channel=None):
        """Record the log message in the log channel if it's not there already"""
        after = self['datetime'] - datetime.timedelta(days=6, hours=23)
        log = self.log_message
        if log_channel is None:
            log_channel = self.log_channel
        # check log if the log_message is already there
        async for msg in log_channel.history(limit=200, after=after):
            if msg.content == log:
                return
        await self.log_channel.send(log)

    def past(self):
        """Is this event in the past?"""
        return self['datetime'] < datetime.datetime.utcnow()

    async def attendees(self):
        """Return set of enrolled attendees"""
        msg = await self.message()
        out = []
        # TODO: parse message for correct emoji instead of using all reactions
        for rxn in msg.reactions:
            out.extend(await rxn.users().flatten())
        return set(out)

    async def content(self):
        """Return message content"""
        msg = await self.message()
        return msg.content

    async def search(self, phrases):
        """Does this event contain one of the given phases"""
        print('search')
        print(phrases)
        content = (await self.content()).lower()
        print(content)
        for i in phrases:
            if i.lower() in content:
                print(i, content)
                return True
        return False

    async def alert(self, dt_min=None, channel=None, suffix=None, wait=True):
        """Schedule/send event alerts mentioning all attendees.
        option dt_min is time before event in minutes.
        """
        if channel is None:
            channel = getattr(self.cog, 'channel', param.rc('event_channel'))
        channel = self.cog.bot.find_channel(channel)
        dt = self['datetime'] - datetime.timedelta(minutes=dt_min)
        if dt < datetime.datetime.utcnow():
            dt_min = (self['datetime'] - datetime.datetime.utcnow()).seconds // 60
        if suffix is None:
            if dt_min is None:
                suffix = " your event is approaching."
            elif dt_min == 0:
                suffix = " your event is starting now."
            elif dt_min % 60 == 0:
                if dt_min == 60:
                    suffix = " your event is starting in an hour."
                else:
                    suffix = " your event is starting in {:d} hours.".format(dt_min//60)
            elif dt_min > 60:
                if dt_min > 120:
                    suffix = " your event is starting in {:d} hours and {:d} minutes."
                else:
                    suffix = " your event is starting in {:d} hour and {:} minutes."
                suffix = suffix.format(dt_min // 60, dt_min % 60)
                if dt_min % 60 == 1:
                    suffix = suffix[:-2] + '.'
            else:
                if dt_min == 1:
                    suffix = " your event is starting in one minute."
                else:
                    suffix = " your event is starting in {:d} minutes.".format(dt_min)
        if wait:
            await wait_until(dt)
        msg = ' '.join([i.mention for i in await self.attendees()]) + suffix
        await channel.send(msg)

    def set_alerts(self, dts=None, channel=None):
        """Set multiple alerts for list of dt (in minutes)"""
        if self._pending_alerts:
            return
        if dts is None:
            dts = param.rc('event_reminders')[:]
        if self.from_hist:
            delta = self['datetime'] - datetime.datetime.utcnow()
            tmp = [dt for dt in dts if datetime.timedelta(minutes=dt) <= delta]
            if dts != tmp:
                logger.printv('dts changed for event {0.name}'.format(self))
                logger.printv('dts: ' + str(dts))
                logger.printv('new: ' + str(tmp))
            dts = tmp
        for dt in dts:
            self.cog.bot.loop.create_task(self.alert(dt, channel=channel))
        self._pending_alerts = True

    async def log_and_alert(self, dts=None, event_chanel=None, log_channel=None):
        """Record log_message and set alerts"""
        await self.record_log(log_channel=log_channel)
        self.set_alerts(dts=dts, channel=event_chanel)


class Events(commands.Cog):
    """Cog to handle events"""
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
        """Return channel and fetch it if needed"""
        if hasattr(self._channel, 'id'):
            return self._channel
        channel = self.bot.find_channel(self._channel)
        if channel:
            self._channel = channel
            return channel

    @property
    def log_channel(self):
        """Return log channel and fetch it if needed"""
        if hasattr(self._log_channel, 'id'):
            return self._log_channel
        channel = self.bot.find_channel(self._log_channel)
        if channel:
            self._log_channel = channel
            return channel

    @property
    def event_list(self):
        """Return a list of active events still to happen"""
        return [e for e in self._events if not e.past()]
    
    def cleanse_old(self):
        """Remove past events"""
        old = [e for e in self._events if e.past()]
        for e in old:
            self._events.remove(e)

    def is_event_channel(self, channel):
        """Is the given channel the event channel"""
        if type(self.channel) == int:
            return channel.id == self.channel
        if hasattr(self.channel, "lower"):
            return channel.name == self.channel
        return channel == self.channel

    @commands.Cog.listener()
    async def on_message(self, message):
        """Parse messages for new event post"""
        # ignore all messages from our bot
        if message.author == self.bot.user:
            return
        # if we have not already parsed the history, do so
        if not self._hist_checked:
            await self.check_history()
        # ignore commands when checking for events
        try:
            if message.content.startswith(self.bot.command_prefix):
                return
        except TypeError:
            for prefix in self.bot.command_prefix:
                if message.content.startswith(prefix):
                    return
        # if message in event channel, than try to parse it
        if self.is_event_channel(message.channel):
            event = _Event(message, self)
            # if this is a valid event
            if event:
                if event not in self._events:
                    self._events.append(event)
                    await event.log_and_alert(event_chanel=self.channel)

    async def check_history(self, channel=None):
        """Check event channel history for any events we missed before we were
        initiated"""
        if channel is None:
            channel = self.channel
        # only check the last week
        after = datetime.datetime.utcnow() - datetime.timedelta(days=6, hours=23)
        try:
            async for i in channel.history(after=after, limit=200):
                event = _Event(i, self, from_hist=True)
                # if valid event
                if event:
                    if event not in self._events:
                        self._events.append(event)
                        await event.log_and_alert(event_chanel=channel)
            logger.printv('History parsed.')
            self._hist_checked = True
        except AttributeError as e:
            logger.error('FAILURE in check_history:\n' + str(e))

    @commands.group()
    async def events(self, ctx):
        """<"attendees"> Lists events and optionally attendees."""
        if ctx.invoked_subcommand is None:
            msg = '{0}) {1.log_message}'
            msg = '\n'.join([msg.format(i + 1, e) for i, e in enumerate(self.event_list)])
            if msg:
                await ctx.send(msg)
            else:
                await ctx.send('No events.')

    @events.command()
    async def attendees(self, ctx):
        """Prints event attendees. Subcommand of events; usage 'TDT$events attendees'"""
        msg = []
        fmt = '{0}) {1.name}: {2}'
        for i, e in enumerate(self.event_list):
            users = [j.display_name for j in await e.attendees()]
            msg.append(fmt.format(i + 1, e, ', '.join(users)))
        msg = '\n'.join(msg)
        if msg:
            await ctx.send(msg)
        else:
            await ctx.send('No events.')

    @events.command()
    async def dt(self, ctx):
        """Prints time until events. Subcommand of events; usage 'TDT$events dt'"""
        try:
            msg = []
            now = datetime.datetime.utcnow()
            fmt = '{0}) {1.name}: {2}'
            for i, e in enumerate(sorted(self.event_list, key=lambda x: x['datetime'])):
                dt = e['datetime'] - now
                msg.append(fmt.format(i + 1, e, dt))
            msg = '\n'.join(msg)
            if msg:
                await ctx.send(msg)
            else:
                await ctx.send('No events.')
        except Exception as e:
            logger.error(e)
            logger.error(''.join(traceback.format_tb(e.__traceback__)))
            raise e

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(5)
        await self.check_history()

    @commands.command()
    async def traitor(self, ctx, n: int = 1, multi: bool = False):
        """Assign and DM a traitor'"""
        t_msg = 'Traitor: You are the Traitor! Turn on your HUD, try to get the Power ' \
                'Ammo, and ready your Knives and Grenades!'
        i_msg = 'Innocent: There is a traitor amongst you... Keep your HUD and Ghost ' \
                'off and be sure to mute if you die.'
        phrases = ['TTT', 'terrorist', 'traitor']
        await self.assign_rolls(ctx, t_msg, i_msg, phrases, n=n, multi=multi)

    @commands.command()
    async def infected(self, ctx, n: int = 1, multi: bool = False):
        """Assign and DM an infected'"""
        a_msg = 'You are the Prime Infected: get out your Stay Away and sword and start '\
                'infecting. You loose your Stay Away after one kill.'
        b_msg = 'Survivor: You’re a survivor... stay alert, they\'re coming...'
        phrases = ['Infection', 'infected']
        await self.assign_rolls(ctx, a_msg, b_msg, phrases, n=n, multi=multi)

    async def assign_rolls(self, ctx, a_msg, b_msg, phrases, n=1, multi=False):
        """Assign and DM a event rolls'"""
        event_name = phrases[0]
        events = [i for i in self.event_list if await i.search(phrases)]
        if len(events) > 1 and not multi:
            raise ValueError('Multiple {:} events registered.'.format(event_name))
        elif not len(events):
            raise ValueError('No {:} events registered.'.format(event_name))

        sent = False
        suf = ''
        for i, e in enumerate(events):
            if len(events) > 1:
                suf = ' ({:})'.format(i)
            attendees = await e.attendees()
            roll_a = random.sample(attendees, n)
            for person in attendees:
                channel = person.dm_channel
                if not channel:
                    await person.create_dm()
                    channel = person.dm_channel
                if person in roll_a:
                    await channel.send(a_msg + suf)
                    sent = True
                else:  # has roll b
                    await channel.send(b_msg + suf)

        if sent:
            logger.printv('Event roll DM(s) sent.')
            await ctx.send('Event roll DM(s) sent.')
        else:
            raise RuntimeError('No event roll messages sent.')


def setup(bot):
    bot.add_cog(Events(bot))
