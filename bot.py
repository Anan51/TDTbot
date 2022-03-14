import asyncio
import datetime
import discord
from discord.ext import commands
from glob import glob
import logging
import os
import pytz
import sys
import traceback
from . import param
from . import helpers
from . import async_helpers
from . import git_manage
from .config.users import get_all_user_config_files, UserConfig


logger = logging.getLogger('discord.' + __name__)
intents = discord.Intents.all()


def cog_list():
    """Returns list of the python files in the cog directory that don't start with '_'"""
    out = os.path.join(os.path.split(__file__)[0], 'cogs', '*.py')
    return [i for i in glob(out) if os.path.split(i)[-1][0] != '_']


class MainBot(commands.Bot):
    """The class that is the TDTbot"""
    def __init__(self, *args, reissue=None, startup=None, **kwargs):
        self.reissue = reissue
        self.startup = datetime.datetime.now() if startup is None else startup
        # set some defaults for the bot
        if 'intents' not in kwargs:
            kwargs['intents'] = intents
        if 'command_prefix' not in kwargs:
            kwargs['command_prefix'] = param.rc('cmd_prefix')
        if 'loop' not in kwargs:
            # create a new loop by default. This makes the __main__ loop work.
            # Otherwise we run into issues reusing a closed loop.
            kwargs['loop'] = asyncio.new_event_loop()
        kwargs['case_insensitive'] = True
        super().__init__(*args, **kwargs)
        self._emoji_role_data = []
        # add all our cogs via load_extension
        for cog in cog_list():
            # ensure that cogs is a submodule of our base module
            cog = __package__ + '.cogs.' + os.path.split(cog)[-1].split('.')[0]
            self.load_extension(cog)

        @self.event
        async def on_ready():
            """Do something when the bot is ready and active... like say so."""
            msg = 'We have logged in as {0.user}, running discord.py {1.__version__}'
            logger.printv(msg.format(self, discord))
            # also we can set a non-custom type activity. This is a discord limitation.
            activity = discord.Activity(name='your suggestions and issues, DM me',
                                        type=discord.ActivityType.listening)
            await self.change_presence(activity=activity)
            if self.reissue is not None:
                logger.printv('Reissue detected.')
                now = pytz.utc.localize(datetime.datetime.now())
                await asyncio.sleep(1)
                hour, week = helpers.hour, helpers.week
                look_back = min(now - hour, self.startup, git_manage.last_updated())
                log = git_manage.git_log_items(look_back=max(look_back, now - week))
                logger.printv('Reboot complete.')
                channel = self.find_channel(self.reissue.channel.id)
                if log:
                    await channel.send("Reboot complete. Git updates detected:")
                    await async_helpers.split_send(channel, log, style='```')
                else:
                    await channel.send("Reboot complete.")
            self.reissue = None
            self.startup = pytz.utc.localize(datetime.datetime.now())

        @self.event
        async def on_command_error(ctx, error):
            """Print errors to the discord channel where the command was given"""
            await ctx.send(str(error))
            raise error

        @self.event
        async def on_raw_reaction_add(payload):
            """Handle emoji reactions"""
            for args_, kwargs_ in self._emoji_role_data:
                await self.emoji2role(payload, *args_, **kwargs_)

        @self.event
        async def on_raw_reaction_remove(payload):
            """Handle emoji reactions"""
            kwargs = {}
            for args_, kwargs_ in self._emoji_role_data:
                kwargs.update(kwargs_)
                kwargs['delete'] = True
                await self.emoji2role(payload, *args_, **kwargs)

    async def bot_check(self, ctx):
        """Run a check to see if we should respond to the given command."""
        if ctx.channel.name in param.rc('ignore_list'):
            return False
        return True

    def find_channel(self, channel):
        """Attempts to return a Channel type object from different types of inputs"""
        # if int assume it's an id number
        if type(channel) == int:
            out = self.get_channel(channel)
            if out is not None:
                return out
            for guild in self.guilds:
                out = guild.get_channel(channel)
                if out is not None:
                    return out
        # if string-like assume it's a channel name in a guild we're in
        if hasattr(channel, 'lower'):
            out = [helpers.find_channel(i, channel) for i in self.guilds]
            out = [i for i in out if i]
            if out:
                return out[0]
        # id is an attribute of the channel type, so we should be good
        if hasattr(channel, 'id'):
            return channel

    async def on_command_completion(self, ctx):
        logger.debug('Command "{0.command}" invoked by {0.author}.'.format(ctx))

    async def on_command_error(self, ctx):
        logger.error('Command "{0.command}" failed. Invoked by {0.author}.'.format(ctx))

    async def get_user_configs(self):
        files = get_all_user_config_files()

        async def get_user(fn):
            return await self.fetch_user(int(os.path.split(fn)[-1].split('.')[0]))

        return [UserConfig(await get_user(f)) for f in files]

    async def get_or_fetch_user(self, user_id, guild=None, fallback=False):
        if isinstance(guild, discord.ext.commands.Context):
            guild = guild.guild
        if isinstance(guild, int):
            try:
                guild = [i for i in self.guilds if i.id == guild][0]
            except IndexError:
                guild = None
        if guild is not None:
            out = guild.get_member(user_id)
            if out is not None:
                return out
            try:
                out = await guild.fetch_member(user_id)
            except discord.errors.NotFound:
                out = None
            if out is not None:
                return out
        out = self.get_user(user_id)
        if out is not None:
            return out
        try:
            out = await self.fetch_user(user_id)
        except discord.errors.NotFound:
            out = None
        if fallback and out is None:
            return user_id
        return None

    def enroll_emoji_role(self, *args, **kwargs):
        """Enroll a function to handle an emoji reaction"""
        if not args:
            raise ValueError("Must provide at least one argument")
        if not isinstance(args[0], dict):
            raise ValueError("First argument must be a dict")
        self._emoji_role_data.append((args, kwargs))

    async def emoji2role(self, payload, emoji_dict, emoji=None, message_id=None,
                         member=None, guild=None, min_role=None, delete=False,
                         remove=None):
        """Handle an emoji reaction"""
        if message_id is not None:
            if payload.message_id != message_id:
                return
        if self.user.id in [payload.user_id, (payload.member, 'id', None)]:
            return
        if guild is None:
            guild = [g for g in self.guilds if g.id == payload.guild_id][0]
        if type(guild) == int:
            guild = self.guilds[guild]
        if member is None:
            member = payload.member
            if member is None:
                member = await self.get_or_fetch_user(payload.user_id, guild)
        if min_role is not None and not delete:
            if not isinstance(min_role, discord.Role):
                min_role = helpers.find_role(guild, min_role)
            if member.top_role < min_role:
                return
        if emoji is None:
            emoji = payload.emoji
        if 1:# member is None:
            data = dict(payload=payload, emoji_dict=emoji_dict, emoji=emoji, message_id=message_id,
                        member=member, guild=guild, min_role=min_role, delete=delete, remove=remove)
            data = {i: j for i, j in data.items() if j is not None}
            msg = "Member is None object"
            msg += '\n' + '\n'.join(['{}: {}'.format(i, j) for i, j in data.items()])
            logger.printv(msg)

        keys = [i for i in emoji_dict if helpers.emotes_equal(i, emoji)]
        if len(keys) == 1:
            key = keys[0]
            role0 = emoji_dict[key]
            role = helpers.find_role(guild, role0)
            if remove is not None:
                if not isinstance(remove, list) and not isinstance(remove, tuple):
                    remove = [remove]

                for i in remove:
                    if not isinstance(i, discord.Role):
                        i = helpers.find_role(guild, i)
                    if i == role:
                        continue
                    await member.remove_roles(i)
            try:
                if delete:
                    await member.remove_roles(role)
                else:
                    await member.add_roles(role)
                return role
            except AttributeError as e:
                logger.printv('Role attr err: {}->{}->{}'.format(key, role0, role))
        elif len(keys) > 1:
            logger.printv('Multiple matches: {}'.format({i: emoji_dict[i] for i in keys}))

    def tdt(self):
        for g in self.guilds:
            if g.id == 164589623459184640:
                return g

    def restart_time(self):
        t = self.startup
        try:
            t = max(t, pytz.utc.localize(self.reissue.message.created_at))
        except AttributeError:
            pass
        return t
