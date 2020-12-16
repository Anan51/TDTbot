import asyncio
import datetime
import discord
import time


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


async def sleep(dt):
    now = datetime.datetime.now()
    try:
        await asyncio.sleep(dt)
    except discord.HTTPException:
        dt -= (datetime.datetime.now() - now).total_seconds()
        time.sleep(dt)
    return


async def admin_check(ctx, bot=None):
    a = ctx.author
    print('admin_check', a, a.top_role)
    if a.top_role.name in ['Admin']:
        return True
    if ctx.guild.owner == a:
        return True
    if bot is not None:
        if await bot.is_owner(a):
            return True
    await.ctx.send('Must be an admin to issue this command.')
    return False
