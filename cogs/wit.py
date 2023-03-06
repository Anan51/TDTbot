import discord  # type: ignore # noqa: F401
from discord.ext import commands  # type: ignore
import asyncio
import datetime
import random
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
        self._init_finished = False
        self._gold = None

    async def _async_init(self):
        if self._init:
            return
        await self.clean_manual_page(None)
        self._init = True
        guild = self.bot.tdt()
        try:
            self._gold = [e for e in guild.emojis if e.name == "gold"][0]
        except IndexError:
            pass
        self._init_finished = True

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(5)
        await self._async_init()

    @property
    def gold(self):
        return self._gold if self._gold else ":gold:"

# blind_beggar

    @commands.command()
    async def blind_beggar(self, ctx):
        msg = """**Blind Beggar**
- A man sat next to a small caravan perks up as you approach. "Oh please, champion." the man says in a dehydrated voice "spare some coin for a blind man?" You look the man up and down. He is wearing a tattered yellow shawl with withered greyish brown shorts.
**Give him a Coin** tdt$blind_gift
**Leave him** tdt$blind_leave
🔐 Silver Tongue:||**Draw Your Weapon** tdt$blind_hostile||"""
        await ctx.send(msg)

    @commands.command()
    async def blind_gift(self, ctx):
        msg = """You give the man a coin and go about your way."""
        await ctx.send(msg)

    @commands.command()
    async def blind_leave(self, ctx):
        msg = """You purse your lips at the man. You pat your satchel to make sure it hasn't been lifted and go about your way."""
        await ctx.send(msg)

    @commands.command()
    async def blind_hostile(self, ctx):
        msg = """You deftly draw your weapon on the man. Despite the weapon making no noise the man reacts immediately "wait!... I m-mean." You brandish your weapon aggressively at him, "What a sorry excuse of a human, faking blindness. You disgust me. Get out of here! Go on!" The man springs to his feet and scrambles away in a hurry, leaving 2 coins behind (+2 """
        msg += (self.gold+" )")
        await ctx.send(msg)

# fracturing_cliff

    @commands.command()
    async def fracturing_cliff(self, ctx):
        msg = """**__Fracturing Cliff__**
- The Reach suddenly shifts underneath you. It sounds like a massive forest all being snapped in half at once... the edge of the bone cliff is fracturing underneath your feet!
**RUN!** tdt$cliff_run
**Hunker Down** tdt$cliff_hunker
🦊 Fenric: ||**Dash Across the Rubble** tdt$cliff_dash||"""
        await ctx.send(msg)

    @commands.command()
    async def cliff_run(self, ctx):
        msg = """You manage to reach the other side of the porous white cliff face. In your haste you may have pulled an ankle. ( 🎲 < 5: Remove ⚡ from a move for the rest of your run)"""
        await ctx.send(msg)

    @commands.command()
    async def cliff_hunker(self, ctx):
        msg = """You cling to the side of the cliff face, the bone shatters, splints, and falls away around you. You are mostly unscathed except for a few shards that cut into your back. ( 🎲 < 4: -1 ❤️ )"""
        await ctx.send(msg)

    @commands.command()
    async def cliff_dash(self, ctx):
        msg = """You nimbly sprint along the cliff face and make it safely to the other side. You're feeling pretty good about yourself (Gain +1 🎲 on all random encounter rolls)"""
        await ctx.send(msg)

# Blood Puddle
    @commands.command()
    async def blood_puddle(self, ctx):
        msg = """**__Blood Puddle__**
- As you continue through the forest, you come to a small grove of trees that are unlike the rest. These trees have red leaves and trunks and they are particular swarmed with insects... more than normal. You breach the thicket and find a puddle of blood. You remember hearing that that Giant's Marrow is a rare resource.
**Collect Some Giant's Blood** tdt$blood_collect
**Leave the Clearing** tdt$blood_leave
🦷 Giant: ||**Drink from the Pool** tdt$blood_drink|| """
        await ctx.send(msg)

    @commands.command()
    async def blood_collect(self, ctx):
        msg = """You grab one of your empty water satchels and draw close to the pool, but before you can even get the lid off your satchel you are attacked! ( 🎲 < 8: use tdt$reach_2 | 🎲 > 9: +5 <:gold:1058304371940655185>)"""
        await ctx.send(msg)

    @commands.command()
    async def blood_leave(self, ctx):
        msg = """You decide to leave the pool alone and let nature figure out what to do with it"""
        await ctx.send(msg)

    @commands.command()
    async def blood_drink(self, ctx):
        msg = """You hesitantly cup your hands and drink from the pool. It taste bitter but you feel it resonate with your pulse. (gain +❤️ and +🔷)"""
        await ctx.send(msg)

# Clingweed

    @commands.command()
    async def clingweed(self, ctx):
        msg = """**__Clingweed__**
- The bone has fallen away here. Previous travelers have set up a rudimentary bridge to cross the gap. You begin carefully crossing over the pit when something sticky brushes against your leg. You try to pull your leg through it but the more you struggle the more it sticks to your flesh. Your movement awakens more of this Clingweed to your presence and its reaching tendrils are closing in on your position FAST.
**Sever the Vines** tdt$cling_cut
**Relax your Body** tdt$cling_relax
🌿 Earthen: ||**Command the Plant** tdt$cling_command||"""
        await ctx.send(msg)

    @commands.command()
    async def cling_cut(self, ctx):
        msg = """You draw your weapon and destroy the tendrils attaching to your flesh. ( 🎲 < 4: Lose your passive for the rest of the run | 🎲 > 5: Lose 3 🔷)"""
        await ctx.send(msg)

    @commands.command()
    async def cling_relax(self, ctx):
        msg = """You conclude the plant is drawn to motion and struggling. You try to relax. The plants reach towards you slows!.. but it doesnt stop. Before you realize it you are surrounded with vines each with a sticky sap like substance on their leaflets you attempt to fight back but its too late, your are slowly being pulled down against the bridge. ( 🎲 < 7: a teammate may spend 1 🔷 for you to try again otherwise: lose your passive for the rest of the run)"""
        await ctx.send(msg)

    @commands.command()
    async def cling_command(self, ctx):
        msg = """You speak an ancient language to the clingweed. It obeys. You command it to wrap one of its blooms around your back for protection... it wants to obey, but its malnourished. (You may spend 6 🔷 to upgrade your Earthen passive to: __Blooming__ 🌸 "Whenever you __Heal__ recover MP as well" for the rest of the run)"""
        await ctx.send(msg)

# Shin Splints

    @commands.command()
    async def shin_splints(self, ctx):
        msg = """**__Shin Splints__**
- You are rather mindlessly walking along the worn path. The sun is beating down against your head through the ravine of trees. You are keeping your eyes on the path but when you looks back up you see a field of bone-forged spears planted and fastened into the ground. The spears are pointed towards your approach, and they look sharp.
**Squeeze Past Them** tdt$shin_squeeze
**Swat Them out of the Way** tdt$shin_swat
📚 Educated: ||**Remove a Spear** tdt$shin_remove||"""
        await ctx.send(msg)

    @commands.command()
    async def shin_squeeze(self, ctx):
        msg = """You carefully sidle through the field of spears, a few of them catch your clothing. ( 🎲 < 3: -2 ❤️ | 🎲 > 4: -2 <:gold:1058304371940655185>)"""
        await ctx.send(msg)

    @commands.command()
    async def shin_attack(self, ctx):
        msg = """You Raise your weapon and begin smashing through the spears. Splinters fly in every direction and a few fly towards your face ( 🎲 < 7: -2 ❤️)"""
        await ctx.send(msg)

    @commands.command()
    async def shin_remove(self, ctx):
        msg = """You squat down along the first row of spears, they are crudely made BUT not flimsily made. You recognize a few of the markings and knots used on the fastenings; they are fenric. "That makes sense" you say out loud to yourself. You think you might be able to remove one of the spears ( 🎲 < 6: failure | 🎲 > 7: Acquire one **Relentless Fang** from the Loot Table)"""
        await ctx.send(msg)

    @commands.command()
    async def champions_landing_boss(self, ctx):
        msg = """__**THE GATEKEEPER**__
❤️ : 15 x👥
💰 : !r 1d3 Lesser
Behavior: Shields are Immune to Precision and Piercing damage
—————————————————
1-3   | **Swat** 💥💥 to ALL players
4-8   | **Prevent** (-3 🎲) 🛡️🛡️x👥 🔀 +❤️
9-10 | **Looming** (+2 🎲) Gain __Empower__
11+    | **Flatten** (-8 🎲) 💥🚫🛡️ to ALL players 🔀 skip their turn"""
        await ctx.send(msg)

    @commands.command()
    async def reach_boss(self, ctx):
        msg = """__**THE GREAT SERPANT**__
❤️ : 20 x 👥
💰 : 2d10 basic
Behavior: gain permanent __Empower__ for every 5 damage taken
—————————————————
1-2   | **Fangs** (+1  🎲) 💥🎯 to the highest HP player
3-7   | **Scales** (-2 🎲) 🛡️🛡️🛡️ x 👥
8-10 | **Weep** (+4 🎲) Cause __Weak__x3 to ALL players
11+   | **Hypnotic Speech** (-4 🎲) summon a random enemy"""
        await ctx.send(msg)

    @commands.command()
    async def reach_enemy(self, ctx):
        encounters = [
            """__**RED WING**__
❤️ : 2
💰 : 1 <:gold:1058304371940655185>
Behavior: take 1/2 damage, rounds down
—————————————————
1-2   | **Peck** 💥💥⚡to the highest HP player
3-8   | **Flap** (+5 🎲) <:stealthIcon:943248201790677052>
9-10 | **Caw** (-10 🎲) Summon another Red Wing""",

            """__**MARROW MITE**__
❤️ : 8
💰 : 1d5 lesser
Behavior: at 2 HP become immune for the rest of the turn
—————————————————
1-6   | **Gnaw** (+2 🎲) 💥💥 to a random player 🔀❤️
7-8   | **Curl** (-2 🎲) 🛡️🛡️🛡️🛡️🛡️
9-10 | **Burrow** leave the encounter and yield no loot""",

            """__**SPINED CONSTRICTOR**__
❤️ : 5
💰 : 4 <:gold:1058304371940655185>
Behavior: successful attacks makes the target lose their next turn
—————————————————
1-3   | **Wrap** (-2 🎲) 💥 random player
4-7   | **Slither** (+5 🎲) 🛡️🛡️<:stealthIcon:943248201790677052>
8-10 | **Spray Venom** (-3 🎲) 💥 to ALL players 🔀 Cause __Burn__x5""",

            """__**MUSTARD SLUG**__
❤️ : 6
💰 : 1d5 lesser
Behavior: taking damage causes __vulnerable__ to the attacker
—————————————————
1-3   | **Corrosive Sludge** (-2 🎲) 💥💥🎯 random player
4-7   | **Gas** (+5 🎲) 🛡️ 🔀  __Vulnerable__ to ALL players
8-10 | **Mucous** (-3 🎲) Cause __Vulnerable__x3 to ALL players""",

            """__**FENRIC THUG**__
❤️ : 8
💰 : 1d7 lesser
Behavior: When this takes damage, gain <:stealthIcon:943248201790677052> for the rest of the turn
—————————————————
1-3   | **Shiv** (+2  🎲) 💥💥⚡ random player
4-7   | **Shifty** (+4 🎲) 🛡️🛡️🔀 Cause __Weak__
8-10 | **Mug** 💥 🚫 lowest HP 🔀 lose 1 <:gold:1058304371940655185>""",

            """__**MALOKOLYTES**__
❤️ : 4
💰 : 1d6 basic
Behavior: upon death, summon another malocolyte with half of your max HP (unless max is 1)
—————————————————
1-3   | **Sacrificial Dagger** (-6 🎲) 💥💥💥 random player
4-9   | **Bad Omen** (+6 🎲) 🛡️🛡️
10     | **Dark Ritual** (-6 🎲) ⚡ double your current max HP""",

            """__**CONFUSED ADVENTURERS**__
❤️ : 10
💰 : 1d10 lesser
Behavior: May be immediately defeated if you have the Silver Tongued passive
—————————————————
1-4   | **Spear** 💥🛡️🎯 random player
5-8   | **Defend** 🛡️🛡️ to ALL PvEnemies
9-10 | **Courage** (-3 🎲) Give __Empower__ to ALL PvEnemies""",

            """__**MARROW MINERS**__
❤️ : 12
💰 : 1d5 basic
Behavior: after 5 turns, cause 💥🚫 to all players
—————————————————
1-3   | **Pickaxe** (+2 🎲) 💥💥 lowest HP player 🔀 -5 🎲
4-7   | **Hardhat** 🛡️🛡️🛡️ 🔀 gain __Heal__
8-10 | **Greed** (-10 🎲) Gain __Empower__x2 for every 10 <:gold:1058304371940655185> your party has""",
        ]
        await ctx.send(random.choice(encounters))


if usingV2:
    async def setup(bot):
        cog = Wit(bot)
        await bot.add_cog(cog)
else:
    def setup(bot):
        bot.add_cog(Wit(bot))
