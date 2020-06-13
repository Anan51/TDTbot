import discord
import inspect
from . import param


def _no_args(*args, **kwargs):
    print(inspect.stack()[1].function)
    if args or kwargs:
        raise ValueError('Arguments passed to a function expecting no arguments.')


async def hello(message, *args, **kwargs):
    """Says "Hello!"."""
    try:
        _no_args(*args, **kwargs)
    except ValueError:
        pass
    await message.channel.send('Hello!')


async def guild(message, *args, **kwargs):
    try:
        _no_args(*args, **kwargs)
    except ValueError:
        pass
    await message.channel.send(message.guild.name)


def inactivity(message, *args, **kwargs):
    words = message.content.split(' ')
