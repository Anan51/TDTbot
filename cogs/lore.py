import discord
from discord.ext import commands
from .. import param
import random
import logging

logger = logging.getLogger('discord.' + __name__)


class Lore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def lore(self, ctx):
        """
        Lore
        """
        with open(param.rc('lore_file'), 'r') as f:
            content = f.read()
            lores = [i for i in content.split('\n\n') if i]
        await ctx.send(random.choice(lores))


def setup(bot):
    bot.add_cog(Lore(bot))
