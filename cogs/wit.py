import discord  # type: ignore # noqa: F401
from discord.ext import commands  # type: ignore
import asyncio
import datetime
from ..helpers import find_channel, find_role, localize
from ..param import emojis, messages, roles
from ..version import usingV2
# from ..async_helpers import admin_check
import logging


logger = logging.getLogger('discord.' + __name__)

class Wit(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot
        self._init = False

    #async def _async_init(self):
    #    if self._init:
    #        return
    #    await self.clean_manual_page(None)
    #    self._init = True

    #@commands.Cog.listener()
    #async def on_ready(self):
    #    await asyncio.sleep(5)
    #    await self._async_init()

    @commands.command()
    async def blind_beggar(self, ctx):
        msg = """**Blind Beggar**
                 - A man sat next to a small caravan perks up as you approach. "Oh please, champion." the man says in a dehydrated voice "spare some coin for a blind man?" You look the man up and down. He is wearing a tattered yellow shawl with withered greyish brown shorts.
                 **Give him a Coin** tdt$blind_gift
                 **Leave him** tdt$blind_leave
                 ||**Draw Your Weapon** tdt$blind_hostile||"""
        ctx.send(msg)

    @commands.command()
    async def blind_gift(self, ctx):
        msg = """You give the man a coin and go about your way."""
        ctx.send(msg)

    @commands.command()
    async def blind_leave(self, ctx):
        msg = """You purse your lips at the man. You pat your satchel to make sure it hasn't been lifted and go about your way."""
        ctx.send(msg)

    @commands.command()
    async def blind_hostile(self, ctx):
        msg = """You deftly draw your weapon on the man. Despite the weapon making no noise the man reacts immediately "wait!... I m-mean." You brandish your weapon aggressively at him, "What a sorry excuse of a human, faking blindness. You disgust me. Get out of here! Go on!" The man springs to his feet and scrambles away in a hurry, leaving 2 coins behind (+2 :gold:)"""
        ctx.send(msg)


if usingV2:
    async def setup(bot):
        cog = Wit(bot)
        await bot.add_cog(cog)
else:
    def setup(bot):
        bot.add_cog(Wit(bot))
