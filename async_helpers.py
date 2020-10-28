import discord


async def split_send(channel, message, deliminator='\n', n=2000, style=''):
    if not message:
        return
    if not type(message) in [tuple, list]:
        message = message.split(deliminator)
    msg = message.pop(0)
    while message:
        tmp = message.pop(0)
        if len(msg + deliminator + tmp + style * 2) >= n:
            await channel.send(style + msg + style)
            msg = tmp
        else:
            msg += deliminator + tmp
    await channel.send(style + msg + style)
