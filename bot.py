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

    async def emoji2role(self, payload, emoji_dict, emoji=None, message_id=None,
                         member=None, guild=None, min_role=None):
        if member is None:
            member = payload.member
        if min_role is not None:
            if member.top_role < min_role:
                return
        if message_id is not None:
            if payload.message_id != message_id:
                return
        if emoji is None:
            emoji = payload.emoji
        if guild is None:
            guild = [g for g in self.guilds if g.id == payload.guild_id][0]
        if type(guild) == int:
            guild = self.guilds[guild]

        keys = [i for i in emoji_dict if helpers.emotes_equal(i, emoji)]
        if len(keys) == 1:
            key = keys[0]
            role = helpers.find_role(guild, emoji_dict[key])
            try:
                await member.add_roles(role)
                return role
            except AttributeError as e:
                logger.printv('Role attr err: {}->{}'.format(key, role))
                logger.printv('      member : "{}"'.format(member))
                logger.printv(payload)
                logger.printv(e)
        elif len(keys) > 1:
            logger.printv('Multiple matches: {}'.format({i: emoji_dict[i] for i in keys}))
