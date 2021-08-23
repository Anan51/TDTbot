import asyncio
import datetime
import discord
import humanize
import logging
import pytz
import time
from . import git_manage, roles

logger = logging.getLogger('discord.' + __name__)


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


async def admin_check(ctx=None, bot=None, author=None, guild=None):
    if author is None:
        if ctx is None:
            raise ValueError("Either ctx or author must be specified")
        author = ctx.author
    if guild is None:
        guild = ctx.guild
    logger.debug('admin_check', author, author.top_role)
    if author.top_role.id in [roles.admin, roles.devoted]:
        return True
    if guild is not None:
        if guild.owner == author:
            return True
    if bot is not None:
        if await bot.is_owner(author):
            return True
    # await ctx.send('Must be an admin to issue this command.')
    return False


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


async def git_log(channel, *args):
    """Print git log to discord chat."""
    await split_send(channel, git_manage.git_log_items(), style='```')
