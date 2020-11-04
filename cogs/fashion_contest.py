import discord
from discord.ext import commands
import logging
import re
import numpy as np
from ..helpers import *
from ..async_helpers import *
from .. import param
from ..config import UserConfig


logger = logging.getLogger('discord.' + __name__)

_channel = param.rc('fashion_channel', default='debugging')
_bot_key = 'tdt.fashion.entries'


class _Entry:
    _emotes = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
    _scores = np.arange(len(_emotes), dtype=int) + 1

    def __init__(self, message_id, author_id, cog):
        self.id = message_id
        self.author_id = author_id
        self.key = ':'.join([str(i) for i in [message_id, author_id]])
        self.cog = cog

    def __repr__(self):
        return '{} {}'.format(str(type(self)), self.key)

    async def message(self):
        """Fetch and return the message associated with this event"""
        # we fetch this every usage to update the reactions
        return await self.cog.channel.fetch_message(self.id)

    async def name(self):
        print('name 0')
        msg = await self.message()
        if msg.content:
            return msg.content.split(':')[-1]
        data = parse_message(msg)
        for i in data['attachments']:
            if i[-1].startswith('image/'):
                return i[0].filename
        out = str(msg.created_at)
        print('name 1')
        return out

    async def votes(self):
        message = await self.message()
        voted = []
        votes = np.zeros(5, dtype=int)
        for rxn in message.reactions:
            if rxn.emoji in self._emotes:
                users = [u async for u in rxn.users() if u != self.cog.bot.user and u not in voted]
                votes[self._emotes.index(rxn.emoji)] += len(users)
                voted += users
        return votes

    async def add_reactions(self):
        msg = await self.message()
        for i in self._emotes:
            await msg.add_reaction(i)

    async def score_stats(self):
        votes = await self.votes()
        if not votes:
            return dict(n=0, mean=0., votes=votes, std=np.nan, total=0)
        mean = np.average(self._scores, weights=votes)
        std = np.sqrt(np.average((self._scores - mean)**2, weights=votes))
        total = np.sum(self._scores * votes)
        return dict(n=votes.sum(), mean=mean, votes=votes, std=std, total=total)

    async def summary(self):
        print('sum 0')
        data = await self.score_stats()
        out = ", ".join(['{}: {}'.format(i, data[i]) for i in ['n', 'mean', 'total']])
        print('sum 1')
        return out


class FashionContest(commands.Cog):
    """Cog designed for fashion contest"""
    def __init__(self, bot):
        self.bot = bot
        self._channel = _channel
        self._entries = None
        self._bot_config = None

    @property
    def bot_config(self):
        if self._bot_config is None:
            self._bot_config = UserConfig(self.bot.user)
            self._bot_config.set_if_not_set(_bot_key, [])
        return self._bot_config

    @property
    def channel(self):
        return self.bot.find_channel(_channel)

    async def enroll_entry(self, entry):
        await entry.add_reactions()
        try:
            self._entries.append(entry)
        except AttributeError:
            self._entries = [entry]
        if entry.key not in self.bot_config[_bot_key]:
            self.bot_config[_bot_key] += [entry.key]

    async def _get_saved_entries(self):
        saved = self.bot_config[_bot_key]
        for i in saved:
            message_id, author_id = [int(j) for j in i.split(':')]
            await self.enroll_entry(_Entry(message_id, author_id, self))

    async def _can_run(self, ctx):
        return ctx.channel == self.channel

    async def cog_check(self, ctx):
        return await self._can_run(ctx)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if not await self._can_run(message):
            return
        if self._entries is None:
            await self._get_saved_entries()
        # await message.channel.send(str(message))
        data = parse_message(message)
        for i in data['type']:
            if i.startswith('image/'):
                await self.enroll_entry(_Entry(message.id, message.author.id, self))

    @commands.command()
    async def list_user_posts(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        if self._entries is None:
            await self._get_saved_entries()
        entries = {i: (await i.message()).created_at for i in self._entries
                   if i.author_id == member.id}
        ordered = sorted(entries, key=entries.get)
        fmt = '{:d}) {} - '
        txt = [fmt.format(i, await e.name(), await e.summary())
               for i, e in enumerate(ordered)]
        print(txt)
        await split_send(self.channel, txt, style="```")


def setup(bot):
    bot.add_cog(FashionContest(bot))
