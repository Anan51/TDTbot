import discord
from discord.ext import commands
from ..helpers import *
import logging


logger = logging.getLogger('discord.' + __name__)

_channel = 562412283268169739
_emojis = ['👍', '💩']


class Lenny(commands.Cog):
    """Cog for Lenny Laboratory posts"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Parse messages for new memes and add reactions"""
        # ignore non-lenny channels
        if message.channel.id != _channel:
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
        data = parse_message(message)
        for i in data['type']:
            for kind in ['image/', 'video/', 'url']:
                if i.startswith(kind):
                    for e in _emojis:
                        await message.add_reaction(e)
                    break

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Count reactions and pin or delete based on counts"""
        if payload.channel_id != _channel:
            return
        if not [emotes_equal(payload.emoji, e) for e in _emojis]:
            return
        channel = self.bot.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        count = {e: 0 for e in _emojis}
        for rxn in msg.reactions:
            for e in _emojis:
                if emotes_equal(rxn.emoji, e):
                    count[e] = rxn.count
        if count[_emojis[1]] >= 6:
            await msg.delete()
        elif count[_emojis[0]] >= 21:
            await msg.pin()
            await msg.add_reaction("🌶️")


def setup(bot):
    bot.add_cog(Lenny(bot))
