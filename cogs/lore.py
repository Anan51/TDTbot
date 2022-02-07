import discord
from discord.ext import commands
from .. import param
import random
import logging
import re

logger = logging.getLogger('discord.' + __name__)
_regex = r"### ?(?P<title>(?:\s?\w)+?) ?(?P<number>[IVXLCM]+)\n(?P<card>(?:.+\n?)+)"


def format_card(card):
    title = (card['title'] + ' ' + card['number']).strip()
    return f"**{title}**\n{card['card']}"


def roman_num(number):
    """Function to convert integer to Roman values"""
    num = [1, 4, 5, 9, 10, 40, 50, 90,
           100, 400, 500, 900, 1000]
    sym = ["I", "IV", "V", "IX", "X", "XL",
           "L", "XC", "C", "CD", "D", "CM", "M"]
    i = 12
    out = ""

    while number:
        div = number // num[i]
        number %= num[i]

        while div:
            out += sym[i]
            div -= 1
        i -= 1
    return out


class Lore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def lore(self, ctx, *args):
        """
        Lore
        """
        with open(param.rc('lore_file'), 'r') as f:
            content = f.read()
        lores = re.finditer(_regex, content, re.MULTILINE)
        if not args:
            return await ctx.send(random.choice(lores))
        else:
            num = None
            try:
                if str(int(args[-1])) == args[-1].strip():
                    title = ' '.join(args)
                    num = roman_num(int(args[-1]))
                else:
                    raise ValueError
            except ValueError:
                title = " ".join(args)
            title = title.lower().strip()
            cards = [i for i in lores if i['title'].lower().strip() == title]
            if num:
                cards = [i for i in cards if i['number'] == num.upper()]
            return await ctx.send(random.choice(cards))


def setup(bot):
    bot.add_cog(Lore(bot))
