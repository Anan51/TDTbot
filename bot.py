import asyncio
import discord
from discord.ext import commands
from glob import glob
import os
from . import param
from . import helpers


def cog_list():
    out = os.path.join(os.path.split(__file__)[0], 'cogs', '*.py')
    return [i for i in glob(out) if os.path.split(i)[-1][0] != '_']


class MainBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        if 'command_prefix' not in kwargs:
            kwargs['command_prefix'] = param.rc('cmd_prefix')
        if 'loop' not in kwargs:
            kwargs['loop'] = asyncio.new_event_loop()
        super().__init__(*args, **kwargs)
        for cog in cog_list():
            cog = __package__ + '.cogs.' + os.path.split(cog)[-1].rstrip('.py')
            self.load_extension(cog)

        @self.event
        async def on_ready():
            msg = 'We have logged in as {0.user}, running discord.py {1.__version__}'
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

    def find_channel(self, channel):
        if type(channel) == int:
            return self.get_channel(int)
        if hasattr(channel, 'lower'):
            out = [helpers.find_channel(i, channel) for i in self.guilds]
            out = [i for i in out if i]
            if out:
                return out[0]
        if hasattr(channel, 'id'):
            return channel
        raise KeyboardInterrupt
