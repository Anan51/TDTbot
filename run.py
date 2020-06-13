import discord
from . import param, ear, functions

client = discord.Client()


def parse_message(message, prefix=None, trim=True):
    if prefix is None:
        prefix = param.rc['cmd_prefix']
    words = list(filter(None, message.content.split(' ')))
    args = []
    kwargs = dict()
    if prefix:
        if not words[0].startswith(prefix):
            return args, kwargs
    if trim:
        words[0].lstrip(prefix)
    for word in words:
        if '=' in word:
            key, item = word.split('=')
            if key in kwargs:
                if type(kwargs[key]) != list:
                    kwargs[key] = [kwargs[key], item]
                else:
                    kwargs[key].append(item)
        else:
            args.append(word)
    return args, kwargs


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.content.startswith(param.rc['cmd_prefix']):
        return

    if not ear.listener.hears(message):
        return

    args, kwargs = parse_message(message)
    function = getattr(functions, args.pop(0).lstrip(param.rc['cmd_prefix']))

    if not function or not callable(function):
        message.channel.send('Unable to parse command.')
        await functions.help()
        return

    await function(message, *args, **kwargs)
    return


def run(token=None):
    if token is None:
        token = param.rc['token']
    if not token:
        raise ValueError('No token provided.')
    client.run(token)
