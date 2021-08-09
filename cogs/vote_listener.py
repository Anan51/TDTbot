import discord
from discord.ext import commands
from ..helpers import *
import logging


logger = logging.getLogger('discord.' + __name__)
_listeners = {562412283268169739: {'react_with': '🌶️'},      # lenny_laboratory
              746441485917880330: {'emojis': ['🌶️', '💩']}}  # spicy_clips


class Listener:
    def __init__(self, channel_id, emojis=None, react_with=None, kinds=None, pin_tresh=20,
                 del_thresh=5):
        self.channel_id = channel_id
        self.emojis = ['👍', '💩'] if emojis is None else emojis
        self.react_with = react_with
        self.kinds = []
        self.kinds.extend(['image/', 'video/', 'url'] if kinds is None else kinds)
        self.pin_tresh = pin_tresh
        self.del_thresh = del_thresh

    def voting_message(self, message):
        if 'any' in self.kinds:
            return True
        data = parse_message(message)
        for i in data['type']:
            for kind in self.kinds:
                if i.startswith(kind):
                    return True
        if 'text_only' in self.kinds:
            return True
        return False

    async def init_votes(self, message, check_first=True):
        if check_first:
            if not self.voting_message(message):
                return
        for e in self.emojis:
            await message.add_reaction(e)

    async def parse_votes(self, payload, bot):
        if not [emotes_equal(payload.emoji, e) for e in self.emojis]:
            return
        channel = bot.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        count = {e: 0 for e in self.emojis}
        ive_reacted = 0
        # check reactions
        for rxn in msg.reactions:
            for e in self.emojis:
                if emotes_equal(rxn.emoji, e):
                    count[e] = rxn.count
                    if rxn.me:
                        ive_reacted += 1
                        # ignore bot reactions in the count
                        count[e] -= 1
        # if the bot hasn't posted the correct reactions this isn't a voting post
        if ive_reacted < len(self.emojis):
            msg = 'Not official vote: {} < {}.'
            logger.printv(msg.format(ive_reacted), len(self.emojis))
            return
        if count[self.emojis[1]] >= self.del_thresh:
            await msg.delete()
        elif count[self.emojis[0]] >= self.pin_tresh:
            await msg.pin()
            if self.react_with:
                await msg.add_reaction(self.react_with)


class VoteListener(commands.Cog):
    """Cog for Lenny Laboratory posts"""
    def __init__(self, bot):
        self.bot = bot
        self.listeners = {key: Listener(key, **_listeners[key]) for key in _listeners}

    @commands.Cog.listener()
    async def on_message(self, message):
        """Parse messages for new memes and add reactions"""
        # ignore channels we are not listening
        try:
            listener = self.listeners[message.channel.id]
        except KeyError:
            return
        # ignore commands
        try:
            if message.content.startswith(self.bot.command_prefix):
                return
        except TypeError:
            for prefix in self.bot.command_prefix:
                if message.content.startswith(prefix):
                    return
        # ignore messages from this bot
        if message.author == self.bot.user:
            return
        await listener.init_votes(message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Count reactions and pin or delete based on counts"""
        try:
            listener = self.listeners[payload.channel_id]
        except KeyError:
            return
        await listener.parse_votes(payload, self.bot)


def setup(bot):
    bot.add_cog(VoteListener(bot))
