import asyncio
import datetime
import discord


async def split_send(channel, message, deliminator='\n', n=2000, style=''):
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
