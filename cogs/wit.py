import discord  # type: ignore # noqa: F401
from discord.ext import commands  # type: ignore
import asyncio
# import datetime
import random
# from ..helpers import find_channel, find_role, localize
# from ..param import emojis, messages, roles
from ..version import usingV2
from ..async_helpers import split_send
import logging


logger = logging.getLogger('discord.' + __name__)


def parse_roll(roll_str, max_sides=None):
    out = [int(e) for e in roll_str.split("d")]
    if max_sides:
        out[1] = min(out[1], max_sides)
    if not out[0]:
        out[0] = 1
    return out


def roll(*args, max_sides=None):
    if len(args) == 1 and hasattr(args[0], "lower"):
        args = parse_roll(args[0], max_sides=max_sides)
    return [random.randint(1, args[1]) for _ in range(args[0])]


def gen_weapon(roll_str):
    prefixes = [
        "**Basic**: No bonus",
        "**Ornate**: +10 in <:gold:1058304371940655185> value",
        "**Lightweight**: +⚡",
        "**Relentless**: +🚫",
        "**Honed**: +🎯",
        "**Heavy**: +🛡️",
        "**Invigorating**: 🔀 +🔷",
        "**Vital**: 🔀 +❤️",
        "**Concealed**: + <:stealthIcon:943248201790677052>",
        "**Superior**: +💥/ +🛡️ / +effect",
    ]
    weapons = [
        "**Knife**: 💥",
        "**Buckler**: 🛡️🛡️",
        "**Kunai**: 💥⚡ ",
        "**Axe**: 💥🚫 ",
        "**Crossbow**: 💥🎯",
        "**Halberd**: 💥🛡️ ",
        "**Focus Stone**: 💥🔀+🔷",
        "**Siphon Stone**: 💥🔀+❤️ ",
        "**Fang**: 💥<:stealthIcon:943248201790677052> ",
        "**Broadsword**: 💥💥",
        "**Spell Book** (-3 🔷): Grant ALL allies any effectx4",
        "**Wand** (-4 🔷): Double a target's active effect stacks",
        "**Runic Flintlock** (-1 🔷):💥; 1/6 chance to TRIPLE successful damage",
        "**Graven Shield** (-1 🔷): 🛡️🛡️ to ALL allies, ignores 🚫",
        "**Gilded Hammer** (-2 🔷): 🛡️🛡️ 🔀 💥 to ALL enemies per block",
        "**Tome** (-4 🔷): Summon a Dire Wolf",
        "**Scroll** (-4 🔷): Your next turn is twice as powerful",
        "**Enchanted Blade** (-4 🔷): 💥💥💥 to ALL enemies",
        "**Staff** (-2 🔷): deal 💥 per each friendly effect stack you have ",
        "REDACTED]]",
    ]
    rolls = zip(roll(roll_str, max_sides=len(prefixes)), roll(roll_str, max_sides=len(weapons)))
    return [(prefixes[r[0] - 1], weapons[r[1] - 1], (r[0] if r[0] != 2 else 10) + r[1]) for r in rolls]


def gen_potion(roll_str):
    prefixes = [
        "**Tincture of**: -Effect",
        "**Potion of**: No bonus",
        "**Tonic of**: Roll Potion Effect list twice, -Effect",
        "**Elixir of**: +Effect",
        "**Grand Mixture of**: ++Effect",
        "**Splash Tincture of**: -Effect to ALL allies/enemies",
        "**Splash Potion of**: to ALL allies/enemies",
        "**Splash Tonic of**: Roll Potion Effect list twice, -Effect, to ALL allies/enemies",
        "**Splash Elixir of**: +Effect to ALL allies/enemies",
        "**Grand Splash Mixture of**: ++Effect to ALL allies/enemies]",
    ]
    potions = [
        "**Regeneration**: +50% ❤️ ( +/-25% per effect prefix)",
        "**Rejuvenation**: +50% 🔷 ( +/-25% per effect prefix)",
        "**Strength**: Empower x3",
        "**Toughness**: Protect x3",
        "**Healing**: Heal x5",
        "**Weakness**: Weak x3",
        "**Sapping**: Vulnerable x3",
        "**Flames**: Burn x5",
        "**Frost**: Skip your targets next 1 turn(s)",
        "**Proficiency**: +🚫🎯⚡ for the next 1 turn(s)",
        ]
    rolls = zip(roll(roll_str, max_sides=len(prefixes)), roll(roll_str, max_sides=len(potions)))
    return [(prefixes[r[0] - 1], potions[r[1] - 1], r[0] + r[1]) for r in rolls]


def gen_artifact(roll_str):
    artifacts = [
        "**Ring of Momentum**: 💍 Kills grant Empower x3",
        "**Safety Hook**: 🪝 Gain Protect whenever a shield fails to block damage",
        "**Vitamins**: 💊 Start each combat with Heal",
        "**Lucky Clover**: 🍀 All enemies gain Weak x2 the first time you run out of MP",
        "**War Drum**: 🥁 All enemies have Vulnerable when you are at 1/2 your max HP",
        "**Eternal Lantern**: 🪔 Attacking causes __Burn__ if you took no damage this turn",
        "**Cook Book**: 🍔 You may raise your max HP and MP by 1 at Camp Sites instead of resting",
        "**Safety Scissors**: ✂️ Once per world, you may escape an encounter or combat, go to the next level, but award no loot. May not be used on a boss ",
        "**Port-a-Forge**: 🛠️ You may upgrade one item or skill (give it the \"Superior\" prefix) for 10 gold whenever you arrive at a shop ",
        "**Ancient Key**: 🗝️ Double the loot you can store this run",
    ]
    return [(None, artifacts[r - 1], r) for r in roll(roll_str, max_sides=len(artifacts))]


def item_card(item, gold=None):
    import re
    gold_str = ""
    prefix, kind, price = item
    if gold is not None and gold is not False:
        gold = 0 if gold is True else gold
        gold += price
        gold_str = f" ({gold} <:gold:1058304371940655185>)"
    if prefix is None:
        name = re.match(r"\*\*(.*)\*\*", kind).group(1)
        return f"**__{name}__**{gold_str}\n{kind}"
    else:
        name = re.match(r"\*\*(.*)\*\*", prefix).group(1) + " " + re.match(r"\*\*(.*)\*\*", kind).group(1)
        return f"**__{name}__**{gold_str}\n{prefix}\n{kind}"


def gen_shop():
    items = gen_weapon("3d19")
    items.extend(gen_potion("3d10"))
    items.extend(gen_artifact("3d10"))
    return [item_card(item, gold=5) for item in items]


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
        return self._gold if self._gold else "<:gold:1058304371940655185>"

# blind_beggar
    @commands.command()
    async def blind_beggar(self, ctx):
        encounters = ['blind_beggar_a',
                      'blind_beggar_b',
                      ]
        encounter = getattr(self, random.choice(encounters))
        return await encounter(ctx)

    @commands.command()
    async def blind_beggar_a(self, ctx):
        msg = """**Blind Beggar**
- A man sat next to a small caravan perks up as you approach. "Oh please, champion." the man says in a dehydrated voice "spare some coin for a blind man?" You look the man up and down. He is wearing a tattered yellow shawl with withered greyish brown shorts.
**Give him a Coin** tdt$blind_gift
**Leave him** tdt$blind_leave
🔐 Silver Tongue:||**Draw Your Weapon** tdt$blind_hostile||"""
        await ctx.send(msg)

    @commands.command()
    async def blind_beggar_b(self, ctx):
        msg = """**__Blind Beggar__**
- A man sat next to a small caravan perks up as you approach. "Oh please, champion." the man says in a dehydrated voice "spare some coin for a blind man?" You look the man up and down. He is wearing a tattered yellow shawl with withered greyish brown shorts.
**Give him a Coin** tdt$blind_gift
**Leave him** tdt$blind_leave
:droplet: Annointed: ||**Draw Your Weapon** tdt$blind_threaten||"""
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
    async def blind_threaten(self, ctx):
        msg = """You deftly draw your weapon on the man. He doesnt respond. You know this man isnt trying to trick you. You say a quick prayer then you give the man some money. He hears the coins hit the bag and says "oh thank you! May YHWH bless your kindness. (You may spend 20 :gold: to upgrade your Annointed passive to: __Angel__ :rosette: "Protect persists, taking damage removes __Protect__ first" for the rest of the run)"""
        await ctx.send(msg)

    @commands.command()
    async def blind_hostile(self, ctx):
        msg = """You deftly draw your weapon on the man. Despite the weapon making no noise the man reacts immediately "wait!... I m-mean." You brandish your weapon aggressively at him, "What a sorry excuse of a human, faking blindness. You disgust me. Get out of here! Go on!" The man springs to his feet and scrambles away in a hurry, leaving 2 coins behind (+2 <:gold:1058304371940655185>)"""
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
        msg = """You manage to reach the other side of the porous white cliff face. In your haste you may have pulled an ankle. (  🎲 ≤ 5: Gain: Limping 🩼  "Gain -1 🎲 to all future encounter rolls)"""
        await ctx.send(msg)

    @commands.command()
    async def cliff_hunker(self, ctx):
        msg = """You cling to the side of the cliff face, the bone shatters, splints, and falls away around you. You are mostly unscathed except for a few shards that cut into your back. ( 🎲 ≤ 4: -25% ❤️ )"""
        await ctx.send(msg)

    @commands.command()
    async def cliff_dash(self, ctx):
        msg = """You nimbly sprint along the cliff face and make it safely to the other side. You're feeling pretty good about yourself (Start all combat with __Empower__)"""
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
        msg = """You grab one of your empty water satchels and draw close to the pool, but before you can even get the lid off your satchel you are attacked! (🎲 ≤ 8: use tdt$reach_enemy | 🎲 ≥ 9: +10 <:gold:1058304371940655185>)"""
        await ctx.send(msg)

    @commands.command()
    async def blood_leave(self, ctx):
        msg = """You decide to leave the pool alone and let nature figure out what to do with it (do another encounter)"""
        await ctx.send(msg)

    @commands.command()
    async def blood_drink(self, ctx):
        msg = """You hesitantly cup your hands and drink from the pool. It taste bitter but you feel it resonate with your pulse. (gain +25% ❤️ and + 25%🔷)"""
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
        msg = """You draw your weapon and destroy the tendrils attaching to your flesh. ( :game_die: ≤ 7: You or a teammate may spend 1 :heart: for you to try again otherwise: Gain: __Sapped__ :zzz: "Disable all other passives")"""
        await ctx.send(msg)

    @commands.command()
    async def cling_relax(self, ctx):
        msg = """You conclude the plant is drawn to motion and struggling. You try to relax. The plants reach towards you slows!.. but it doesnt stop. Before you realize it you are surrounded with vines each with a sticky sap like substance on their leaflets you attempt to fight back but its too late, your are slowly being pulled down against the bridge. ( :game_die: ≤ 7: You or a teammate may spend 1 :heart: for you to try again otherwise: Gain: __Sapped__ :zzz: "Disable all other passives" )"""
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
**Swat Them out of the Way** tdt$shin_attack
📚 Educated: ||**Remove a Spear** tdt$shin_remove||"""
        await ctx.send(msg)

    @commands.command()
    async def shin_squeeze(self, ctx):
        msg = """You carefully sidle through the field of spears, a few of them catch your clothing. ( 🎲 ≤ 3: -25% ❤️ | 🎲 ≥ 4: -6 <:gold:1058304371940655185>)"""
        await ctx.send(msg)

    @commands.command()
    async def shin_attack(self, ctx):
        msg = """You Raise your weapon and begin smashing through the spears. Splinters fly in every direction and a few fly towards your face ( 🎲 ≤ 7: -25% ❤️ )"""
        await ctx.send(msg)

    @commands.command()
    async def shin_remove(self, ctx):
        msg = """You squat down along the first row of spears, they are crudely made BUT not flimsily made. You recognize a few of the markings and knots used on the fastenings; they are fenric. "That makes sense" you say out loud to yourself. You think you might be able to remove one of the spears ( 🎲 ≤ 6: failure | 🎲 ≥ 7: Acquire one **Invigorating Fang** from the Loot Table)"""
        await ctx.send(msg)

    @commands.command()
    async def champions_landing_boss(self, ctx):
        msg = """__**THE GATEKEEPER**__
❤️ : 15 x👥
💰 : !r 1d3 Lesser
Behavior: Shields are Immune to Precision and Piercing damage
—————————————————
1-3   | **Swat** 💥💥 to ALL players
4-8   | **Prevent** (-2 🎲) 🛡️🛡️x👥 🔀 +❤️
9-10 | **Looming** (+2 🎲) Gain __Empower__
11+    | **Flatten** (-8 🎲) 💥🚫🛡️ to ALL players 🔀 skip their turn
https://www.youtube.com/watch?v=0uAsD6lQV1I"""
        await ctx.send(msg)

    @commands.command()
    async def reach_boss(self, ctx):
        encounters = [
            """__**THE GREAT SERPENT**__
❤️ : 20 x 👥
💰 : 2d10 basic
Behavior: gain permanent __Empower__ for every 5 damage taken
—————————————————
1-2   | **Fangs** 💥🎯 to the highest HP player
3-7   | **Scales** (-2 🎲) 🛡️🛡️🛡️ x 👥
8-10 | **Weep** (+4 🎲) Cause __Weak__x3 to ALL players
11+   | **Hypnotic Speech** (-4 🎲) summon a random enemy
https://youtu.be/wlF0-Qs2xkI""",

            """__**FLOW-MASTER GRIGORI**__
:heart: : 15 x:busts_in_silhouette:
:moneybag: : 1d19 :dagger:, +6 Comp Points
Behavior: At even minutes this gains a stack of __Protect__ permanently, at odd minutes this gains a stack of __Empower__ permanently.
—————————————————
1-4   | **Beat** (:game_die: = 11) :boom::boom::zap:
5-7   | **Groove** (:game_die: = 1) :shield::shield: :twisted_rightwards_arrows: deal :boom: per blocked
8-10 | **Rhythm** (:game_die: = 5) +3:heart:
11+    | **Change Up** Immune. Nullify all status moves used this turn.
https://www.youtube.com/watch?v=16y1AkoZkmQ""",

            """__**SLIGGO THE GREEN**__
:heart: : 25 x:busts_in_silhouette:
:moneybag: : 3d10 :test_tube:, +6 Comp Points
Behavior: When a player deals damage to this, they gain __Heal__. Sliggo cannot lose more than half its current HP every turn (unless at 1 of course).
—————————————————
1-5   | **Envelop** :boom::boom: Highest HP :twisted_rightwards_arrows: +3 :game_die:, gain __Heal__, target loses 2 :large_blue_diamond:
6-8   | **Absorb** Gain __Heal__x2 per damage taken this turn
9-10 | **Dissolve** (+ 2 :game_die:) Cause __Burn__x3
11+    | **Divide and Conquer** If this has __heal__ greater than its HP, summon another Sliggo with equal stats. Otherwise cause __weak__ and __vulnerable__ and gain __heal__x2
https://www.youtube.com/watch?v=iMH49ieL4es""",
            ]
        await ctx.send(random.choice(encounters))

    @commands.command()
    async def reach_enemy(self, ctx):
        encounters = [
            """__**RED WING**__
❤️ : 2
💰 : 4 <:gold:1058304371940655185>
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
1-6   | **Gnaw** (-1 🎲) 💥💥 to a random player 🔀❤️
7-8   | **Curl** (-2 🎲) 🛡️🛡️🛡️🛡️🛡️
9-10 | **Burrow** leave the encounter and yield no loot""",

            """__**SPINED CONSTRICTOR**__
❤️ : 5
💰 : 6 <:gold:1058304371940655185>
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
8-10 | **Mug** 💥 🚫 lowest HP 🔀 lose 3 <:gold:1058304371940655185>""",

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

# Abandoned Feast
    @commands.command()
    async def abandoned_feast(self, ctx):
        msg = """**__Abandoned Feast__**
- You walk past a stone brick building and decide to check it out. Inside the smell of food greets you as you walk into a massive dining hall with a wide spread of cooked meats, breads, and potatoes adorning the banquet. Your starving but this seems a bit too good to be true...
**Take a small bite** tdt$feast_snack
**Eat as much as you can** tdt$feast_buffet
:mountain_snow: Highlander: ||**Unmatched apatite** tdt$feast_devour||"""
        await ctx.send(msg)

    @commands.command()
    async def feast_snack(self, ctx):
        msg = """You take a few bites of food and leave the rest. (+1 :heart: and +1 :large_blue_diamond:)"""
        await ctx.send(msg)

    @commands.command()
    async def feast_buffet(self, ctx):
        msg = """You try to consume as much as humanly possible... you start to feel sleepy (+4 :heart: and +4 :large_blue_diamond:, 🎲 ≤ 8: go back 3 places in your journey)"""
        await ctx.send(msg)

    @commands.command()
    async def feast_devour(self, ctx):
        msg = """You immediately recognize this feast. This is a traditional highlander feast. You know exactly what to do. (You may spend 7 <:gold:1058304371940655185> to upgrade your Highlander passive to: __True Scottsman__ :scotland: "Your max MP is now equal to your current HP. Gain 50% of your new max MP" for the rest of the run)"""
        await ctx.send(msg)

# Hoisted Sack
    @commands.command()
    async def hoisted_sack(self, ctx):
        msg = """**__Hoisted Sack__**
- Your walking through a man-made trail when a brown sack hanging from a tree catches your eye. Its extremely high up and will take a bit of dexterity to get it down. Or you could just leave it be.
**Climb the Tree** tdt$sack_climb
**Leave the Loot** tdt$sack_leave
:bow_and_arrow: Elvish: ||**Intuition** tdt$sack_search||"""
        await ctx.send(msg)

    @commands.command()
    async def sack_climb(self, ctx):
        msg = """You gather your strength then attempt to reach the sack dangling from the branches. ( 🎲 ≤ 4: summon enemy | 🎲 ≥ 5: !r 1d5 lesser chest)"""
        await ctx.send(msg)

    @commands.command()
    async def sack_leave(self, ctx):
        msg = """You leave the sack. Its probably someone's stuff anyways... (Go back one floor)"""
        await ctx.send(msg)

    @commands.command()
    async def sack_search(self, ctx):
        msg = """You remember using this trick yourself back when you were younger. This is to keep away wild animals which means there is probably a camp not too far nearby. Sure enough after a bit of searching you find an elvish camp. It seems it has been overtaken by some thugs but there is still an Elvish scroll bound around a book that they werent capable of opening. (You may spend 2 :heart: to upgrade your Elvish passive to: __Pure Blood__ :woman_elf: "While an enemy has __Weak__ they cannot cause __effects__")"""
        await ctx.send(msg)

# Fork in the Road
    @commands.command()
    async def fork_in_the_road(self, ctx):
        msg = """**__Fork in the Road__**
- As you continue through the forest, you come to a choice on paths. You can chose to go left which onlooks an array of strange looking plants and trees or right which leads to a rickety bridge. There is another path straight forward but it seems to lead to an outpost which some local bandits have set ablaze.
**Left** tdt$fork_left
**Right** tdt$fork_right
:fire: Draconic: ||**Straight Forward** tdt$fork_straight||"""
        await ctx.send(msg)

    @commands.command()
    async def fork_left(self, ctx):
        msg = """You decide to play it safe and go towards the vegitation. (Do another encounter)"""
        await ctx.send(msg)

    @commands.command()
    async def fork_right(self, ctx):
        msg = """You head towards the bridge. You know its risky but you at least understand your risks. You carefully try to cross the bridge ( 🎲 ≤ 3: -3 ❤️ )"""
        await ctx.send(msg)

    @commands.command()
    async def fork_straight(self, ctx):
        msg = """You were born of fire. You march straight through the outpost, fearlessly. You find some gold in one of the buildings. (Double your current <:gold:1058304371940655185> )"""
        await ctx.send(msg)

# Desperate Traveler
    @commands.command()
    async def desperate_traveler(self, ctx):
        msg = """**__Desperate Traveler__**
- A woman with a broken weapon comes sprinting towards you. She looks panicked and scared. "HELP!" She cries out "Someone help!" you look past her and see a band of vicious looking creatures chasing after her
**Ignore the woman** tdt$traveler_ignore
**Fight the pursuers** tdt$traveler_fight
:mechanical_arm:  Sentian: ||**Deploy Smoke Screen** tdt$traveler_smoke||"""
        await ctx.send(msg)

    @commands.command()
    async def traveler_ignore(self, ctx):
        msg = """You clearly make eye contact with the woman, but dip behind a tree to avoid detection by her pursuers. You are racked with guilt (Gain: __Fearful__ :rooster: Start each combat with __Vulnerable__x3)"""
        await ctx.send(msg)

    @commands.command()
    async def traveler_fight(self, ctx):
        msg = """You beckon the woman to stand behind you and prepare for a fight. (Summon a Major, gain a permanent stack of __Protect__ if you win)"""
        await ctx.send(msg)

    @commands.command()
    async def traveler_smoke(self, ctx):
        msg = """You fire a smoke bomb behind the woman. She is fearful at first but understands your intent a moment later. You call her over to a hiding spot. She obeys. Once on the other side of the smoke, the enemies cannot find you and decide to give up. "You saved me." she says with a thick romanian accent. You look down at her and say nothing. "Please..." she fumbles through her bag "take one" she offers you a potion (gain one !r 1d10 potion)"""
        await ctx.send(msg)

    @commands.command()
    async def reach_encounter(self, ctx):
        encounters = ['desperate_traveler',
                      'fork_in_the_road',
                      'hoisted_sack',
                      'abandoned_feast',
                      'shin_splints',
                      'clingweed',
                      'blood_puddle',
                      'fracturing_cliff',
                      'blind_beggar',
                      ]
        encounter = getattr(self, random.choice(encounters))
        return await encounter(ctx)

    @commands.command()
    async def underwash_enemy(self, ctx):
        encounters = [
            """__**UNCLEAN WALKER**__
❤️ : 5
💰 : 1d10 🧪
Behavior: at the end of turn 3, lower all players max HP and MP by 1 for the rest of the run
—————————————————
1-5   | **Breathe** (+2 🎲) __Weak__, __Vulnerable__, __Burn__ to ALL but itself
6-8   | **Fester** (+3 🎲) ⚡🛡️❤️
9-10 | **Spore** (-2 🎲) if you took less than 3 damage this turn, skip all players turns once.""",

            """__**SITE CONTAMINATE PURIFIER**__
❤️ : 8
💰 : 1 Higuard Key + 5 <:gold:1058304371940655185>
Behavior: Immune to negative effects
—————————————————
1-3   | **Secure** 💥💥💥 to the highest HP player 🔀 dispell all __effects__ stacks
4-6   | **Contain** (+2 🎲) ALL players gain __Weak__x3
7-10 | **Protect** (-4 🎲) Disable any active player status moves. All other PvEnemies gain __Protect__x3""",

            """__**TOCK**__
❤️ : 8
💰 : 1d10 🗡️
Behavior: at the end of turn 5, deal 20 damage to everything
—————————————————
1-4   | **Sidearm** 💥⚡🎯
5-8   | **Harden** (+2 🎲) 🛡️🛡️
8-10 | **Beacon** (-5 🎲) if this took no damage this turn, summon another enemy""",

            """__**H3-nry,  THE PROTOTYPE**__
❤️ : 1
💰 : 6 <:gold:1058304371940655185>
Behavior: Summon another henry at the end of every 2 turns
—————————————————
1-3   | **BLAST** 💥💥💥💥 to ALL players
4-8   | **BLAST** 💥💥💥💥 to lowest HP players
9-10 | **BLAST** 💥💥💥💥 to highest HP players""",

            """__**DESPERATE CHAMPION**__
❤️ : 12
💰 : !r 1d7 Basic
Behavior: When this takes damage, gain __Empower__. Can be immediately dismissed if you are doing a Champion Run.
—————————————————
1-4   | **Momentum** (+2 🎲) 💥 lowest HP
5-8   | **Deflect** (+2 🎲) <:stealthIcon:943248201790677052> 🔀 -4 🎲 if you have 🎯
9-10 | **Pin Point** (-2 🎲) Your next 💥 has 🎯""",

            """__**MIMIC NYMPH**__
❤️ : Target's HP
💰 : !r 7d3 <:gold:1058304371940655185>
Behavior: Select a random player at the start of the game. This will only ever attack that
—————————————————
1-3   | **Copy** Use targets first move.
4-6   | **Imitate** Use targets second move.
7-10 | **Plagiarize** Use targets third move.""",

            """__**HIGUARD**__
❤️ : 7
💰 : 1 Higuard Key
Behavior: If this takes 3 or more damage in one turn, summon another Higuard in 2 turns
—————————————————
1-3   | **Polearm** 💥💥🛡️
4-7   | **Sentry Line** 🛡️🛡️ to ALL PvE 🔀 💥
8-10 | **Bolas Shot** (-4 🎲) Cause __Vulnerable__x2 and __Weak__x2""",

            """__**NECROZOAN SLUDGE**__
❤️ : 8
💰 : !r 1d10 basic
Behavior: at 4, 2, and 1 remaining HP summon a copy of itself. Loot only drops for completing the fight.
—————————————————
1-4   | **Infect** 💥 lowest HP 🔀 ❤️, cause __Weak__ and __Will__
5-8   | **Consume** <:stealthIcon:943248201790677052>  🔀 Gain __Protect__
9-10 | **Replicate** All PvEnemies gain __Healing__ for each stack of __Protect__ this has. Remove all protect stacks.""",

            """__**RAZOR FIN**__
❤️ : 10
💰 : !r 1d10 🧪  + 5 <:gold:1058304371940655185>
Behavior: Cannot take more than 4 damage a turn
—————————————————
1-4   | **Thrash** 💥⚡🚫
5-8   | **Submerge** 🛡️🛡️ immune to 🚫
9-10 | **Gills** Dispell all player __effects__ 🔀 gain __Empower__ per dispelled""",

            """__**BLACKHAND GANG MARAUDER**__
❤️ : 8
💰 : 2 Higuard Keys
Behavior: cause Vulnerable whenever gold is stolen per gold stolen
—————————————————
1-2   | **Seeing Red** 💥💥⚡ 🔀 -3 <:gold:1058304371940655185> per damage dealt
3-7   | **Trick Step** Ignore ALL incoming 💥 🔀 -6 🎲; Your next 💥 has 🚫🎯
8-10 | **Sapping Powder** (-2 🎲) ALL players gain -2 🔷""",
        ]
        await ctx.send(random.choice(encounters))

    @commands.command()
    async def underwash_encounter(self, ctx):
        encounters = [
            """**__Card Dealer__**
- You pass by a small collection of people gathered around a a wooden box with some cards on it. On the other side of the box a man with a shaggy coat and white gloves is slinging the cards here and there then asking a disheveled looking fellow on the other side to take a guess. The man thumbs his chin for a bit then reluctantly motions for more cards "OOOoh." The card slinger cries, "Looks like its not your lucky day." The card dealer pockets some gold then he sees you standing there. He eyes up your gold pouch then says "Come on over stranger. Take a card!" (Roll !r 2d11)
**Hit** tdt$card_hit
**Stand** tdt$card_stand
:closed_lock_with_key: Silver Tongue: ||**Slight of Hand** tdt$card_trick||""",
            """**__Purifying Clinic__**
- The street ends at a unkempt medical clinic... at least you think it is. There is a small line of weary and sick looking people out front and a haphazardly placed cross above the door painted in some kind of red paint. A few volunteer guards are standing outside making sure no one decides to try anything drastic. They are under-armed.
**Get Medical Help** tdt$clinic_heal
**Help Some Outside** tdt$clinic_help
📚  Educated: ||**Study and Observe** tdt$clinic_study||""",
            """**__The Salesman__**
- "Potions! Get your high quality Ether Potions here! Finest in the underwash! Straight from the Judges tap!" You are intrigued. You walk over to the man and realize that he is no human. Half of his body has been spliced together with some kind of rat-like Fenric. Below patches of some of his fur are orange scales that, if you didnt know better, looked like scabs. He sees you eyeing him over and says "Hey there. You look like the type that could use a quality potion or two. Here:" he holds out a small flask "On the house." You take a bit of the flask and inquire what it does, the salesman replies "Wonderous things!"... you're dubious
**Take a sip** tdt$salesman_sip
**Take a big gulp** tdt$salesman_gulp
:fire:  Draconic: ||**Smell it** tdt$salesman_smell||""",
            """**__Abandoned Chest__**
- You are sneaking your way through the streets, hoping none of the creatures or Higuard notice you when you come across a small, strangely secluded room with a chest sitting on the far wall. The pace looks abandoned save for a few piles of bones here and there... was this some kind of old dungeon?
**Open the Chest** tdt$chest_open
**Go on your way** tdt$chest_leave
:fox:  Fenric: ||**Listen to the Room** tdt$chest_listen||""",
            """**__Crying Child__**
- You are making your way long the streets when a group of children come out to meet you "Please adventurer" one little girl with golden hair cries out "You have to help us!" The other children look horrified at her. "what areyou doing?" one of the boys say ot her. She keeps looking towards you "Please. Our friend, she's very sick.. she has..." The girl chokes down a sob "She has Necrosis. The doctors wont even see her please she-" the girl covers her face and tears pour through her fingers
**Turn her away** tdt$child_leave
**See what you can do** tdt$child_help
:droplet: Anointed: ||**Pray and Try to Help** tdt$child_pray||""",
            """**__A Strange Sound__**
- You are about to cross over a bridge when you notice that it is out. It looks to have been abandoned for years. After some debate you head towards a large pipe that runs parallel to to the blue river above in the cave ceiling. As you are crossing through, making small splashes in the dirty green water, you hear a strange noise coming from behind you... You stop and listen... Is that?.. WATER! and LOTS of it!
**Run for it** tdt$flood_run
**Find an Off Shoot** tdt$flood_branch
:tooth:  Giant: ||**Brace yourself** tdt$flood_brace||""",
            """**__Quarantined Zone__**
- The underwash has interesting smells. Often times its a sweet but stale smell from the blue liquid, other times its the faint scent of sewage, and other still its a slight hint of herbs and bread. This time however, it smells like chemicals. The type of chemicals only used in a few places, most of them surrounding something dead. The scent is growing stronger as you are stopped by a large blocked off street. Personnel dot the borders of a large yellow and white dome with yellow paper tape crisscrossing the entrances reading "DANGER BIO HAZARD"
**Go around** tdt$zone_around
**Sneak Through** tdt$zone_sneak
:herb:  Earthen: ||**Release Sunshine** tdt$zone_sun||""",
            """**__Rusted Factory__**
- The man on the street corner swears that through this factory is a shortcut to the other side of town. Being that a large stone wall separates you from it, you figure you might as well give it a shot. The factory has long since been abandoned. The smell or rust, oil, and hard water saturates through the breeze... ah... a breeze! Maybe the man was right. You flip an old switch and the factory groans to life again. Lightbulbs buzz and flicker illuminating... most... of the factory. Unfortunately the man did not mention that the hole in the wall is higher up on an inaccessible third floor. You are going to have to get creative...
**Climb Up** tdt$factory_climb
**Find Another Around** tdt$factory_around
:mechanical_arm:   Sentian: ||**Examine the Machines** tdt$factory_examine||""",
            """**__Ferryman__**
- You approach the edge of a slow moving river of clear blue and green liquid. The river stretches from the inside of a pipe in a massive concrete wall to miles down the waterway. You arent going to be able to go around... A man with a cloak standing on top of a small flat raft approach you. "Do you seek to cross?" You cant see his face but you can tell the tone of his voice is one of a tired, withered old man. You nod, forgetting he likely cant see your face either. Nevertheless he responds "You are the ones who broke the seals?" Your pulse quickens for a moment but you slowly reply, "Y-yeah." He doesnt move "Perhaps it is time..." He holds out his hand expectantly.
**Pay in Gold** tdt$ferry_gold
**Pay in Spirit** tdt$ferry_spirit
:bow_and_arrow:  Elvish: ||**Pay in Blood** tdt$ferry_blood||""",
            """**__Tonic Vending Machine__**
- You are walking down the street when something catches your eye. A tall glass and metal machine with a display of tonics bound up by spiral metal tubing inside. Words along the top of it read "AEROR CORP REHYDRATOR". The machine springs to life as you approach a little tune buzzes out of the speakers ( `https://www.youtube.com/watch?v=5vdRHWxSyR8`). You are excited, nay, ecstatic to put a coin in and buy something.
**Buy One (5 Gold)** tdt$vending_one
**Buy Three (15 gold)** tdt$vending_three
:mountain_snow: Highlander: ||**SHOULDER CHARGE** tdt$vending_charge||""",
        ]
        await ctx.send(random.choice(encounters))

    @commands.command()
    async def card_hit(self, ctx):
        msg = """You look at your cards and decide to take another (Roll !r 1d11)"""
        await ctx.send(msg)

    @commands.command()
    async def card_stand(self, ctx):
        msg = """You decide you are happy with your card total. ( Roll !r 3d15, if your card total is greater than this BUT not over 21 you gain 10 <:gold:1058304371940655185>. If not, then lose 10 <:gold:1058304371940655185> )"""
        await ctx.send(msg)

    @commands.command()
    async def card_trick(self, ctx):
        msg = """You suspect trickery is at play here. You eye the amounts being rewarded and being taken and you realize there is about an 80% chance you will lose which doesnt make sense. You watch closely then discover the secret: the man is playing with a trick deck. You are impressed at his cunning if not slightly disgusted at his thievery. You decide to wait a while until everyone else clears out then you ask him to teach you his tricks... for a price of course. (You may spend 20 <:gold:1058304371940655185> to upgrade your Silver Tongue passive to: __Gilded Tongue__ :money_with_wings: "Shops are now 5 gold cheaper, gain 1 <:gold:1058304371940655185> whenever you reach a new level" for the rest of the run)"""
        await ctx.send(msg)

    @commands.command()
    async def clinic_heal(self, ctx):
        msg = """"Hello there." a woman with greasy black hair, dark bags under her eyes, and a smile says to you. "Do you need healing? I can offer my services if you have something in exchange." (10 Gold or 1 Higuard Key to attempt to remove a curse/negative passive: :game_die: ≤ 9 : remove 1 passive)"""
        await ctx.send(msg)

    @commands.command()
    async def clinic_help(self, ctx):
        msg = """"I might be able to help you and your cause" you say to an old woman wearily trying to take care of the line of people. "That-" she looks at her guards "That would be fine, but you need to lay down your weapons." You are nervous about leaving your weapons out in such a public place, but it would be worth it if you can help. (:game_die: ≥ 3 : gain 5 <:gold:1058304371940655185> and give a weapon :twisted_rightwards_arrows: gain __heal__ | :game_die: ≤ 2: discard one weapon )"""
        await ctx.send(msg)

    @commands.command()
    async def clinic_study(self, ctx):
        msg = """"You ask the woman if you can sit and observe how she works. She is clearly skilled in medicines and also working the more complicated machinery. She is hesitant. You offer some gold and keys in exchange for her inconvenience" (You may spend 10 <:gold:1058304371940655185> and 1 Higuard Key to upgrade your Educated passive to: __Scholar__ :brain:  "Recreate your character with an additional 14 :sparkles: to your total" lasts for the rest of this run)"""
        await ctx.send(msg)

    @commands.command()
    async def salesman_sip(self, ctx):
        msg = """You take a timid sip of the liquid. The salesman eyes you over with a smirk on his lips. You begin to feel... something... You look back up to see the salesman has vanished
( :game_die: ≤ 2: lose your primary passive | :game_die: 3-7: nothing happens | :game_die: ≥ 8: gain a second passive (roll 1d10 for it from the creation engines lineage list) )"""
        await ctx.send(msg)

    @commands.command()
    async def salesman_gulp(self, ctx):
        msg = """You drain the flask into your stomach with gusto. The salesman cant help but cackle. "tastes good right?" his mouth flops open and he drools at the thought. He begins to sniff the air "ahhh yes you're in for a ride"
( :game_die: ≤ 5: lose your primary passive | :game_die: ≥ 5: gain a second passive (roll 1d10 for it from the creation engines lineage list) and __Will__x2)"""
        await ctx.send(msg)

    @commands.command()
    async def salesman_smell(self, ctx):
        msg = """You look the salesman in the eye. Your gaze makes him cower slightly. You take a sniff of the flask while maintaining eye contact... the salesman is visibly sweating. "This is a transformation tonic. I can smell my peoples blood in it. Its unmistakable" The salesman begins to fidget with something in his pocket "ahh well, y-you see... th-this is specially designed for uhh-" You hand the liquid back to him "If you wish to leave here alive you better get rid of this right now" His eyes grow wide, then narrow back down and a sneer crawls across his face. "and what are ya gonna do if I dont?" In flash you kick a nearby box into the ally and light it ablaze with a gust from your lungs. Fear grips him as he recoils back. "I-I'm sory I-I-I will g-get rid of it! H-here! Take it! Im sorry! Its yours!" he drops a relic on the table, hastily drops the flask, and scurries away on all fours. (You may spend 4 :heart:  to upgrade your Draconic passive to: __Scale of Ancients__ :dragon_face:   "Blocking an attack causes __Burn__ to the attacker per each damage blocked. Dealing damage to a burning target triggers all its burn damage all at once and removes the Burn stacks" lasts for the rest of this run)"""
        await ctx.send(msg)

    @commands.command()
    async def chest_open(self, ctx):
        msg = """You decide to open the chest. You quietly approach it, looking around for traps. There doesnt seem to be any...
( :game_die: ≤ 9: its a mimic. Fight the enemy in spoiler tags below | :game_die: =10 : huh. its just loot (roll !r d10 lesser))

||__**MIMIC NYMPH**__
:heart: : Target's HP
:moneybag: : !r 7d3 <:gold:1058304371940655185>
Behavior: Select a random player at the start of the game. This will only ever attack that
—————————————————
1-3   | **Copy** Use targets first move.
4-6   | **Imitate** Use targets second move.
7-10 | **Plagiarize** Use targets third move.||"""
        await ctx.send(msg)

    @commands.command()
    async def chest_leave(self, ctx):
        msg = """You decide to leave the chest. Something doesnt feel right. (do another encounter)"""
        await ctx.send(msg)

    @commands.command()
    async def chest_listen(self, ctx):
        msg = """Something in the air clues you in that this isnt a normal chest. You perk up your ears, close your eyes, and listen. You hear the sounds of the wood creaking. The sounds of the waterway rushing outside. The drops of the the Ether seeping in through the stone walls. The sounds of... breathing... Its faint, but you can identify that that breathing is coming from the chest. Its a mimic. You have heard about these and you know how to deal with it. You stand up as tall as you can and begin clanging your weapon on the ground and growling and roaring. You bear your fangs and make as much noise as you can. After a little while, the mimic begins to slowly back away towards a hole in the house, revealing a pile of gold where it was digesting (gain !r 1d10 gold)"""
        await ctx.send(msg)

    @commands.command()
    async def child_leave(self, ctx):
        msg = """You tell the little girl you cant help. "But why!" She cries out holding back sobs. You tell her necrosis is too dangerous and she should find a doctor. "The doctors wont help" she says. You say that you are sorry, but neither can you. ( Gain: __Cold__ :snowflake:  "Take and give 1 less __Healing__ and +:heart:" )"""
        await ctx.send(msg)

    @commands.command()
    async def child_help(self, ctx):
        msg = """You nod and go into the the shack the girl is standing outside of. Inside the situation is dire. The room is dimly lit with candles that are struggling to stay lit under the influence of the necrosis. A woman, about 16-20 years old is neck deep in the thick black substance, its beginning to pin her to the wall and it looks like it has already overtaken her feet completely. The womans hands are restrained to the bed. shards of glass bottles dot the ground, some of them with bits of dried blood on them. "It felt so good at first." The woman says "I wasnt hurting anyone, it just brought me pleasure. Isnt life about finding pleasure?" A chill runs down your spine. "Let me guess, you are going to tell me that this is wrong?" You stare blankly "That I am not allowed to feel this way." You hear something whisper in your mind...

(You can either use your mana to try to sever the woman from the necrosis (!r 1d20, anything below a 12 is a success and you lose 2 stacks of __will__) or you can coax the necorsis onto you (gain 5 stacks of __Will__, gain a Higuard key))"""
        await ctx.send(msg)

    @commands.command()
    async def child_pray(self, ctx):
        msg = """You nod and go into the the shack the girl is standing outside of. Inside the situation is dire. The room is dimly lit with candles that are struggling to stay lit under the influence of the necrosis. A woman, about 16-20 years old is neck deep in the thick black substance, its beginning to pin her to the wall and it looks like it has already overtaken her feet completely. The womans hands are restrained to the bed. shards of glass dot the ground, some of them with bits of dried blood on them. "YOU STAY AWAY FROM ME!" The woman screams. "MARY! THIS MAN IS GOING TO TRY TO HURT ME!" she cries out. The little girl doesnt waver. You walk forward and stretch out your hand towards her head. The chains holding her in place rattle wildly as she tries to reach for bits of broken glass bottles scattered along the floor. You place your hand firmly on her hand and invoke a prayer to YHWH. "NO PLESE! SPARE US! WE NEVER HARMED THE CHILDREN" The womans voice is desperate. A light gleams from your hand as the necrosis scatters or evaporates. You open your eyes to see the woman no longer gripped with the black substance. Shes sobbing. You release her chains. The little girl runs towards her and puts her arms around her. The womans wrists are purple with bruising. The lights flicker as the girl turns towards you and says "Thank you." Her tears no longer stain her shirt. (Lose 10 stacks of __Will__)"""
        await ctx.send(msg)

    @commands.command()
    async def flood_run(self, ctx):
        msg = "You begin a full sprint towards the exit. The water is crashing against the metal pipes behind you as you hear the pipes respond with metalic groans from the weight. The pipe ends in a sheer drop to a drain, there is light shining through it. It will hurt, but you might be able to smash through it and get clear on the other side (🎲 ≤ 5 : -50% ❤️ and go back one level)"
        await ctx.send(msg)

    @commands.command()
    async def flood_branch(self, ctx):
        msg = "You see an off shoot of the main pipe directly above you with a ladder leading up, you muster your strength and jump up to reach it just in time for the watter to blast through the pipe below you. Your feet get drenched, but you are fine. You climb to the top and push off the metallic cover only to see you aer now in the middle of an enemies camp... (Fight a Major, +5 <:gold:1058304371940655185> if you win)"
        await ctx.send(msg)

    @commands.command()
    async def flood_brace(self, ctx):
        msg = "You eye up the water coming towards you and glance behind you to see a drain isnt far off. You scan your environment and see there is a drain above you but the tunnel is too small for you to fit. You decide your best bet is to grab the ladder above and brace for impact. The water is intense, but nothing you cant handle. Despite it being murky, the water smells like only algae inhabits it, and its cool against your skin. (Gain +25% 🔷)"
        await ctx.send(msg)

    @commands.command()
    async def zone_around(self, ctx):
        msg = "You decided to follow the orders and detour around the site. Unfortunately this will set you back pretty severely. (Go back 5 levels)"
        await ctx.send(msg)

    @commands.command()
    async def zone_sneak(self, ctx):
        msg = "You dont have time to waste. You wait for the staff to look away then you cross under the tape and head inside the dome. Inside black and pinkish sludge are growing along the walls. The smell of chemical has fully given way to the smell of rot. You instinctively cover your face. Bodies are strewn about the zone, with some of their corpses slowly climbing up the walls from the sludge. The room in here is well lit with florescent lamps that seem to be dissipating some of the sludge where it is most concentrated leaving a large amorphous scab where it has dried up. Some site containment crews are looking at equipment and scanning the room with strange devices. Others are collecting samples. The longer you stand in here the more you begin to feel light headed... You head for the door.. (:game_die: ≤ 3 : summon 2 Reach enemies | :game_die: ≥ 4 : lose 1 max HP and 1 max MP, gain one stack of __Will__)"
        await ctx.send(msg)

    @commands.command()
    async def zone_sun(self, ctx):
        msg = "You peer through the sheets of the dome's door and see that they are using high intensity lights to clear the infection. You have a bit of sunlight saved from the Reach, you decide to release it here to help them out (Spend 4 :large_blue_diamond:)"
        await ctx.send(msg)

    @commands.command()
    async def factory_climb(self, ctx):
        msg = "You let out a sigh. You knew the shortcut was too good to be true. You loosen your shoulders and start mantling equipment and support beams to climb towards the hole. The metal lurches and creaks with every next step... Maybe... maybe you shouldnt be doing this( Gain +1 to your dice for each :zap: move you have: :game_die: ≤ 6 : fall, -1 :heart: and gain :x_ray: __**Fractured**__: \"Skip your first turn every new combat\"  | :game_die: ≥ 7 : skip ahead 3 levels)"
        await ctx.send(msg)

    @commands.command()
    async def factory_around(self, ctx):
        msg = """"This isnt worth it" you mutter to yourself out loud. You turn around to leave the factory when you are greeted by a band of Sentian marauders. They are rusted and brandishing discarded parts. They do NOT look happy to see you. (Fight 3 of the below enemy)
|| __**RUSTED MARAUDER**__
:heart: : 6
:moneybag: : Safety Scissors or 6 gold
Behavior: When this takes damage or an ally dies, gain __Empower__.
—————————————————
1-4   | **Knife** (+2 :game_die:) :boom: lowest HP
5-8   | **Broken Fang** (+2 :game_die:) :stealthIcon: :twisted_rightwards_arrows: -4 :game_die: if you have :dart:
9-10 | **Hone** (-2 :game_die:) Your next :boom: has :dart:||"""
        await ctx.send(msg)

    @commands.command()
    async def factory_examine(self, ctx):
        msg = """You take a moment to stop and examine the machines. It was hard to see in the dim light but with a little use of your flashlight you can clearly see that the parts scattered around here are Sentian parts. The parts are very old, probably some of the first models ever produced by AEROR corp., even the logo is out of date! Something triggers deep within the recesses of your mind, you mindlessly navigate to a backroom where one machine is still in perfect functioning order. This seems so familiar. The machine is perched in the ceiling and needles and surgery equipment arm its front like teeth. In the chair a smaller Sentian is sat limp with its chest open. Your curiosity gets the better of you as you walk around to the front. The Sentian's chest is open; a human heart is exposed inside. Wires interlock it into place. It beats slowly and meekly. As you try to collect your emotions you notice that a black rot has begun eating away at its lower aorta. Your own heartbeat quickens as the Sentian child looks up at you weakly. You panic and head for the door with a quick step when you are stopped by another taller Sentian holding scissors and bandages.

"We can't save him" it says to you, its eyes looking down at the bandages, "this was his favorite, take it with you to defeat the Evil One." it looks you in your eyes as it holds out a custom made forearm plate. You look down at the equipment. (You may spend 3 :heart: and 7 :gold: to upgrade your Sentian passive to: __AEROR Corp. Classic__ :gear: "Gain __Empower__ for each point of damage you take" lasts for the rest of this run)"""
        await ctx.send(msg)

    @commands.command()
    async def ferry_gold(self, ctx):
        msg = "You dig through your pocket in search of gold. While you are doing so, the man says \"He did not bring the curse\" This gives you pause, but you keep looking (pay 20 Gold or 2 Higuard Keys, if you dont have the currency use tdt$ferry_spirit)"
        await ctx.send(msg)

    @commands.command()
    async def ferry_spirit(self, ctx):
        msg = "You dont elect to provide any currency. You decide to instead grasp his hand. This feels like what was intended, strangely. The man grips your hand firmly and says \"He knows you will kill if it gets you more renown or experience\" (Gain __Will__ x3)"
        await ctx.send(msg)

    @commands.command()
    async def ferry_blood(self, ctx):
        msg = "You examine the mans hand. You notice it has tattoos in old elvish. You dont speak it, but you strangely seem to understand what they are saying. You place the edge of your blade in your hand and cut it. It begins to bleed. You drip some of the blood onto the ferryman's hand \"Sacrifice is the only cure\" he says. The tattoos recede and he retracts his hand. (-2 max HP)"
        await ctx.send(msg)

    @commands.command()
    async def vending_one(self, ctx):
        msg = "You slip a handful of coins into its slot, press its button pad, and eagerly await the machine to dispense your goods. The machine whirrs and sings as it pushes one of the bottles out of the metal tube. Your face lights up as it gets near the edge as you watch with earnest... at this moment in time, all is right in the world. The troubles you have gone through up until this point feel like distant memories. All that matters... right now... is this little cup and the machine that- is stuck? Stuck?! STUCK!?! ( Gain +1 to your dice for each :no_entry_sign: move you have: :game_die: ≤ 3 : Stuck :(  | :game_die: ≥ 4 : select one \"Tonic of\" prefixed potion from the loot table)"
        await ctx.send(msg)

    @commands.command()
    async def vending_three(self, ctx):
        msg = 'You slip a handful of coins into its slot, press its button pad, and eagerly await the machine to dispense your goods. The machine whirrs and sings as it pushes the bottles out of the metal tube. Your face lights up as it gets near the edge as you watch with earnest... at this moment in time, all is right in the world. The troubles you have gone through up until this point feel like distant memories. All that matters... right now... is this little cup and the machine that- is stuck? Stuck?! STUCK!?! ( Gain +1 to your dice for each :no_entry_sign: move you have: :game_die: ≤ 3 : Stuck :(  | :game_die: ≥ 4 : select one "Tonic of" prefixed potion from the loot table. Repeat your rolls for each Tonic)'
        await ctx.send(msg)

    @commands.command()
    async def vending_charge(self, ctx):
        msg = [
            'You slip a handful of coins into its slot, press its button pad, and eagerly await the machine to dispense your goods.',
            'The machine whirrs and sings as it pushes the bottles out of the metal tube.',
            'Your face lights up as it gets near the edge as you watch with earnest...',
            'at this moment in time, all is right in the world.',
            'The troubles you have gone through up until this point feel like distant memories.',
            'All that matters... right now... is this little cup and the machine that- is stuck? Stuck?! STUCK!?!',
            'This will not stand. Your face distorts into concentrated fury.',
            'Your snort and scrunch your face. You backpaddle.',
            'Onlookers watch in horror as what happens next can only be described as an unstoppable force meeting an immovable object.',
            'You wind up and put your FULL body into the machine.',
            'With a crash, the machine detaches from the wall and sails into the air.',
            'Writers of this moment, to this day, swear that the machine moved in slow motion as an chorus of angels accompanied its flight.',
            'Plays, songs, and cinemas were written about this moment in the years to come, always with some details wrong, but the one thing that remained a constant through all of them was the beauty of that moment.',
            'Some say some world leaders had changes of heart after hearing about this moment.',
            'Nations would fall, others would rise, but this moment... is a constant.',
            'Like a manifesto of peace and war. This moment was... poetic.',
            'Your mind becomes lost in the contemplations of the cosmos as the machine -some say it landed on the corners but historians tend to agree it landed face first- shatters upon the cold stone ground.',
            'The cracking of metal and glass rang out for everyone to hear.',
            'They say even Malokai shuddered at the sound of it.',
            'Truly, this was the culmination of the human spirit against the cold uncaring virtues of the system it was placed in. Justice. Truth. Love.',
            'All were made apparent that day.',
            'Truly... this would be the highlight of your life.',
            'It was all downhill from here... You understood this.',
            'How could you possibly follow such a display?',
            'You couldn\'t! A deep sadness underpines your mountain top experience.',
            'But at least for a while... you made your ancestors -and all those who would come after you- proud.',
            '(select one "Tonic of" prefixed potion)',
        ]
        await split_send(ctx, msg, " ")

    @commands.command()
    async def underwash_boss(self, ctx):
        encounters = [
            """__**THE TRAITOR: JUDGE-23**__
:heart: : 14
:moneybag: : 1d19 :dagger:, 1d10 <:gold:1058304371940655185>, 1d10 :test_tube:
Behavior: Summon another JUDGE-23 per :busts_in_silhouette:. Whenever a player gains an __effect__ this gains __Empower__
—————————————————
1-4   | **Heresy** (+1 :game_die:) :boom: targets random players. Repeats 2 times (w buffs applied).
5-7   | **Martyr** (-2 :game_die:) Cause __Weak__x2 to ALL players per damage taken. If this would have died this turn, all players gain __burn__x99 instead.
8-10 | **Doomsayer** If this took no damage, ALL players gain __Vulnerable__ at the start of every turn.
11+   | **Judgement** :boom::boom::boom::no_entry_sign: to ALL. If a player dies, repeat.
https://www.youtube.com/watch?v=bMfvZmhqW0A&pp=ygUTZ29kIHNoYXR0ZXJpbmcgc3Rhcg%3D%3D""",
            """__**LEGION OF FLESH**__
:heart: : 6
:moneybag: : 1d19 :dagger:, +6 Comp Points
Behavior: Summon another Legion of Flesh x :busts_in_silhouette: x 4. They roll/act as one unit but must be targeted individually
—————————————————
1-4   | **Wrath** (:game_die: +4) :boom: lowest HP, repeat per Legion of Flesh
5-7   | **Envy** All other Legion of Flesh gain +:heart: per damage taken
8-10 | **Greed** (:game_die: - 3) If this took no damage, summon another Legion of Flesh
11+    | **Pride** roll `!r 1d<# of Legion>`, That corresponding Legion is invincible until another dies
https://www.youtube.com/watch?v=zP_1e30FWsE""",
            """__**ITS RIGHT HAND**__
:heart: : 20
:moneybag: : 3d10 :test_tube:, +6 Comp Points
Behavior: All players gain __Will__ if this takes any form of damage from a player, per damage taken.
—————————————————
1-3   | **Reaching** (:game_die: -3) :boom::boom::dart: to ALL players :twisted_rightwards_arrows: this gains -:heart::heart:
4-6   | **Pulling** :shield::shield::shield: :twisted_rightwards_arrows: this gains -:heart::heart:
7-10 | **Whispering** (:game_die: +2) If this took no damage, this gains -:heart::heart: and gains __empower__ x2
11+    | **Sinking** all players must do a different encounter from underwash or the reach. This shares your encounter results. Combat is paused until you return.
https://www.youtube.com/watch?v=EKLWC93nvAU""",
        ]
        await ctx.send(random.choice(encounters))

    @commands.command()
    async def blinds_enemy(self, ctx):
        encounters = [
            """__**VOID GOLUM**__
:heart: : 20
:moneybag: : Lose 1 __Will__
Behavior: When this takes damage, attacker loses 1 :large_blue_diamond:
—————————————————
1-3   | **Crush** in 2 turns from now :boom::boom::boom::boom:
4-8   | **Accretion** Gain persistent :shield: per damage taken this turn
9-10 | **Singularity** (-2 :game_die:) in 4 turns from now, deal :boom::boom::boom::boom::boom::boom::dart::no_entry_sign: to ALL :twisted_rightwards_arrows: cause __Will__ x3
https://www.youtube.com/watch?v=FhS2jvMDPv4""",
            """__**∅ HUNTER**__
:heart: : 15
:moneybag: : !r 3d10 :gold:
Behavior: Every turn this doesn't take damage, gain __Empower__. Can be immediately dismissed if fighting Gaidg-3, Naya, or Remus but doing so yields no loot.
—————————————————
1-3   | **Sidestep** (+2 :game_die:) Avoid all :boom: :twisted_rightwards_arrows: take another turn
4-7   | **Fire** :boom::zap::dart:  to ALL
8-10 | **Target Lock** (-2 :game_die:) Double your current __empower__ stacks
https://www.youtube.com/watch?v=CHdHaoPLW9U""",
            """__**EYES IN SILENCE**__
:heart: : 10
:moneybag: : Lose 2 __Will__
Behavior: Immune to direct attacks, cant be targeted directly by effects.
—————————————————
1-3   | **Bleed** (-2 :game_die:) :boom::boom: :no_entry_sign: :twisted_rightwards_arrows: cause __Will__ x1
4-7   | **Suffocate** (+6 :game_die:) Cause __Weak__, __Vulnerable__, and __Will__ to ALL players
8-10 | **Peer** (+2 :game_die:) Summon a Sclera
> **__SCLERA __**
> :heart: : 5 / :boom: : 1
> Upon death, cause -:heart: to ALL Eyes in Silence.
https://www.youtube.com/watch?v=FhS2jvMDPv4""",
            """__**NIHILEACH**__
:heart: : 6
:moneybag: : Lose 1 __Will__
Behavior: Summon 2 more NIHILEACHES; resurrect with 2 HP if the fight doesnt end after 4 turns of each dying. You gain rewards for the summoned NIHILEACHES as well.
—————————————————
1-3   | **Bite** (+2 :game_die:) :boom::dart: :twisted_rightwards_arrows: cause __Will__ per hit
4-5   | **Drain** :boom::zap: :twisted_rightwards_arrows: +:heart: per hit, -4 :game_die:
6-10 | **Chitter** (+2 :game_die:) All other Nihileaches gain __Empower__ and +:heart:
https://www.youtube.com/watch?v=ldFdBiT4VN0""",
            """__**-THE DIFFERENCE -SECOND -DECISION -PERSONALITY -OPEN -UP -IN TWO**__
:heart: : -6
:moneybag: : Lose all __Will__
Behavior: -m3:4Pa62sl
—————————————————
1-4   | **Gloom** (+1 :game_die:) :shield::shield::shield:
5-8   | **Cursed Shield** :boom::boom::boom: :twisted_rightwards_arrows: +:game_die:
9-10 | **Doubt** (+3 :game_die:) Gain __Burn__x3
https://www.youtube.com/watch?v=qMX3aVbNdvo""",
            """__**HYPNOCYTE**__
:heart: : 8
:moneybag: : Lose 3 __Will__
Behavior: If this is alone, flee and yield no loot.
—————————————————
1-6   | **Indulge** (:game_die: + __will__ ) -2:heart: a different enemy :twisted_rightwards_arrows: this gains __will__ x2
4-7   | **Control** (-3 :game_die:) Give all enemies __Empower__, +:heart:, and -:game_die: per every __Will__ this has
8-10 | **Beckon** cause __Will__ per damage taken
https://www.youtube.com/watch?v=H1Fx6rs66yM""",
            """__**ROTTING BEHEMOTH**__
:heart: : 20
:moneybag: : Lose 2 __Will__
Behavior:  :tooth: Giant: ||**Devotion, Bravery, Sacrifice**|| (If you have no __Will__ and beat this fight, upgrade your Giant passive to: __Guardian__ :trident:  "On all future Crusades using Giant, allies can use your encounter paths.")
—————————————————
1-6   | **Stuggle** :boom::boom::boom::boom::boom::boom: :twisted_rightwards_arrows: -:heart: per dealt
7-8   | **Flinch**  Cause __Burn__ per taken :twisted_rightwards_arrows: -:game_die: and __Empower__ per caused
9-10 | **Grow** Double current HP. Gains permanent __Weak__ and +:game_die:.
https://www.youtube.com/watch?v=-4tmO9ZOBn8""",
            """__**PHANTOM OF AGE**__
:heart: : 12
:moneybag: : Lose 4 __Will__
Behavior: This can only take one damage per turn
—————————————————
1-3   | **Early** (+3 :game_die:) :boom::zap::no_entry_sign::dart: :twisted_rightwards_arrows: all PVEnemies gain permanent __Empower__
4-6   | **Prime**  If this took no damage, disable ALL player's passive and statuses for the rest of the fight
8-10 | **Late** (-3 :game_die:) :stealthIcon::shield::twisted_rightwards_arrows: cause __Will__
https://www.youtube.com/watch?v=bK6D94UHP6M""",
            """__**THE WILLESS**__
:heart: : 6
:moneybag: : Summon the last enemy that killed you
Behavior: "Wh-what? Why dont you relax! We are happy this way"
—————————————————
1-3   | **Flesh** ALL gain __Empower__, __Protect__, and __Will__
4-6   | **Eyes** ALL gain +:gold: and __Will__
8-10  | **Life** ALL gain +:heart: and __Will__
https://m.youtube.com/watch?v=yZsfIluYxsA""",
            """__**MESSENGER**__
:heart: : 10
:moneybag: : +50% :heart: and :large_blue_diamond:
Behavior: Gain __Empower__ and __Protect__ for each stack of __Will__ the player's have. This will not fight and is immune to everything unless its alone.
—————————————————
1-3   | **Hope** (-2 :game_die:) :boom::zap: :twisted_rightwards_arrows: Cause __Burn__ per stack of __WIll__ the player's have
4-6   | **Love** (+5 :game_die:) :shield::shield: :twisted_rightwards_arrows: Cause __Weak__ per stack of __WIll__ the player's have
8-10  | **Faith** Gain __Healing__ per stack of __WIll__ the player's have
https://www.youtube.com/watch?v=ze0Rk-m0w2A""",
        ]
        await ctx.send(random.choice(encounters))

    @commands.command()
    async def wit_shop(self, ctx):
        await split_send(ctx, gen_shop(), "\n\n")

    @commands.command(aliases=['r'])
    async def roll(self, ctx, roll_str):
        rolls = roll(roll_str)
        msg = ' + '.join([str(i) for i in rolls])
        if len(rolls) > 1:
            msg += ' = {:}'.format(sum(rolls))
        await ctx.send(msg)

    @commands.command()
    async def floor(self, ctx):
        options = ["💀 Enemy",
                   "☠️ Major",
                   "❔ Encounter",
                   "⛺ Camping Spot",
                   "🛖 Shop"
                   ]
        await ctx.send(', '.join(random.choices(options, weights=[11, 2, 9, 1, 1], k=3)))


if usingV2:
    async def setup(bot):
        cog = Wit(bot)
        await bot.add_cog(cog)
else:
    def setup(bot):
        bot.add_cog(Wit(bot))
