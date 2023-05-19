import discord  # type: ignore # noqa: F401
from discord.ext import commands  # type: ignore
import asyncio
# import datetime
import random
# from ..helpers import find_channel, find_role, localize
# from ..param import emojis, messages, roles
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
        msg = """You deftly draw your weapon on the man. He doesnt respond. You know this man isnt trying to trick you. You say a quick prayer then you give the man some money. He hears the coins hit the bag and says "oh thank you! May YHWH bless your kindness. (-1 <:gold:1058304371940655185> (You may spend 6 <:gold:1058304371940655185> to upgrade your Annointed passive to: __Angel__ :rosette: "Once per combat: if you have __protect__ and your HP reaches zero, lose all stacks but survive with 1 HP." for the rest of the run)"""
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
        msg = """You manage to reach the other side of the porous white cliff face. In your haste you may have pulled an ankle. ( 🎲 < 5: Remove ⚡ from a move for the rest of your run)"""
        await ctx.send(msg)

    @commands.command()
    async def cliff_hunker(self, ctx):
        msg = """You cling to the side of the cliff face, the bone shatters, splints, and falls away around you. You are mostly unscathed except for a few shards that cut into your back. ( 🎲 < 4: -1 ❤️ )"""
        await ctx.send(msg)

    @commands.command()
    async def cliff_dash(self, ctx):
        msg = """You nimbly sprint along the cliff face and make it safely to the other side. You're feeling pretty good about yourself (Start the next combat with __Empower__x2)"""
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
        msg = """You grab one of your empty water satchels and draw close to the pool, but before you can even get the lid off your satchel you are attacked! ( 🎲 < 8: use tdt$reach_enemy | 🎲 > 9: +5 <:gold:1058304371940655185>)"""
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
        msg = """You draw your weapon and destroy the tendrils attaching to your flesh. ( 🎲 < 4: Gain: __Sapped__ 💤 "Disable all other passives" | 🎲 > 5: Lose 3 🔷)"""
        await ctx.send(msg)

    @commands.command()
    async def cling_relax(self, ctx):
        msg = """You conclude the plant is drawn to motion and struggling. You try to relax. The plants reach towards you slows!.. but it doesnt stop. Before you realize it you are surrounded with vines each with a sticky sap like substance on their leaflets you attempt to fight back but its too late, your are slowly being pulled down against the bridge. ( 🎲 < 7: You or a teammate may spend 1 🔷 for you to try again otherwise: Gain: __Sapped__ 💤 "Disable all other passives" )"""
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
11+    | **Flatten** (-8 🎲) 💥🚫🛡️ to ALL players 🔀 skip their turn
https://www.youtube.com/watch?v=0uAsD6lQV1I"""
        await ctx.send(msg)

    @commands.command()
    async def reach_boss(self, ctx):
        encounters = [
            """__**THE GREAT SERPANT**__
❤️ : 20 x 👥
💰 : 2d10 basic
Behavior: gain permanent __Empower__ for every 5 damage taken
—————————————————
1-2   | **Fangs** (+1  🎲) 💥🎯 to the highest HP player
3-7   | **Scales** (-2 🎲) 🛡️🛡️🛡️ x 👥
8-10 | **Weep** (+4 🎲) Cause __Weak__x3 to ALL players
11+   | **Hypnotic Speech** (-4 🎲) summon a random enemy
https://youtu.be/wlF0-Qs2xkI""",

            """__**FLOW-MASTER GRIGORI**__
:heart: : 10 x:busts_in_silhouette:
:moneybag: : 1d19 :dagger:, +6 Comp Points
Behavior: At even minutes this gains a stack of __Protect__ permanently, at odd minutes this gains a stack of __Empower__ permanently.
—————————————————
1-4   | **Beat** (:game_die: = 11) :boom::zap:
5-7   | **Groove** (:game_die: = 1) :shield: :twisted_rightwards_arrows: deal :boom: per blocked
8-10 | **Rhythm** (:game_die: = 5) +3:heart:
11+    | **Change Up** Immune. Nullify all status moves used this turn.
https://www.youtube.com/watch?v=16y1AkoZkmQ""",

            """__**SLIGGO THE GREEN**__
:heart: : 30 x:busts_in_silhouette:
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
        msg = """You try to consume as much as humanly possible... you start to feel sleepy (+4 :heart: and +4 :large_blue_diamond:, 🎲 < 8: go back 3 places in your journey)"""
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
        msg = """You gather your strength then attempt to reach the sack dangling from the branches. ( 🎲 < 5: summon enemy | 🎲 > 5: !r 1d5 lesser chest)"""
        await ctx.send(msg)

    @commands.command()
    async def sack_leave(self, ctx):
        msg = """You leave the sack. Its probably someone's stuff anyways."""
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
        msg = """You head towards the bridge. You know its risky but you at least understand your risks. You carefully try to cross the bridge ( 🎲 < 3: -3 ❤️ )"""
        await ctx.send(msg)

    @commands.command()
    async def fork_straight(self, ctx):
        msg = """You were born of fire. You march straight through the outpost, fearlessly. You find some gold in one of the buildings. (+3 <:gold:1058304371940655185> )"""
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
        msg = """You beckon the woman to stand behind you and prepare for a fight. (Summon two random enemies per party member. Gain __empower__ and __protect__ at the start of THIS combat. Gain a bonus Artifact if you win (one per team))"""
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
❤️ : 10
💰 : 1d10 🗡️
Behavior: Immune to negative effects
—————————————————
1-3   | **Secure** 💥💥 to ALL players 🔀 dispell all __effects__ stacks
4-6   | **Contain** (+2 🎲) ALL players gain __Weak__x3
7-10 | **Protect** (-4 🎲) Disable any active player status moves. All other PvEnemies gain __Protect__x3""",

            """__**TOCK**__
❤️ : 8
💰 : 2d5 <:gold:1058304371940655185>
Behavior: at the end of turn 5, deal 20 damage to everything
—————————————————
1-4   | **Sidearm** 💥⚡🎯
5-8   | **Harden** (+2 🎲) 🛡️🛡️
8-10 | **Beacon** (-5 🎲) if this took no damage this turn, summon another enemy""",

            """__**H3-nry,  THE PROTOTYPE**__
❤️ : 1
💰 : !r 1d3 lesser
Behavior: Summon 1 more Henry's on battle start
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

            """__**HIGAURD**__
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
1-2   | **Thrash** 💥⚡🚫
3-8   | **Submerge** 🛡️🛡️ immune to 🚫
9-10 | **Gills** Dispell all player __effects__ 🔀 gain __Empower__ per dispelled""",

            """__**BLACKHAND GANG MARAUDER**__
❤️ : 4
💰 : 2 Higuard Keys
Behavior: +2 to all dice rolls (including speed ties)
—————————————————
1-2   | **Seeing Red** 💥💥 🔀 -3 <:gold:1058304371940655185> per damage dealt
3-7   | **Trick Step** Ignore 1 incoming 💥 🔀 -6 🎲; Your next 💥 has 🚫🎯
8-10 | **Sapping Powder** (-2 🎲) Random player has -2 🔷""",
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
        ]
        await ctx.send(random.choice(encounters))

    @commands.command()
    async def card_hit(self, ctx):
        msg = """You look at your cards and decide to take another (Roll !r 1d11)"""
        await ctx.send(msg)

    @commands.command()
    async def card_hitcard_stand(self, ctx):
        msg = """You decide you are happy with your card total. ( Roll !r 3d15, if your card total is greater than this BUT not over 21 you gain 10 <:gold:1058304371940655185>. If not, then lose 10 <:gold:1058304371940655185> )"""
        await ctx.send(msg)

    @commands.command()
    async def card_hitcard_trick(self, ctx):
        msg = """You suspect trickery is at play here. You eye the amounts being rewarded and being taken and you realize there is about an 80% chance you will lose which doesnt make sense. You watch closely then discover the secret: the man is playing with a trick deck. You are impressed at his cunning if not slightly disgusted at his thievery. You decide to wait a while until everyone else clears out then you ask him to teach you his tricks... for a price of course. (You may spend 20 <:gold:1058304371940655185> to upgrade your Silver Tongue passive to: __Gilded Tongue__ :money_with_wings: "Shops are now 5 gold cheaper, gain 1 <:gold:1058304371940655185> whenever you reach a new level" for the rest of the run)"""
        await ctx.send(msg)

    @commands.command()
    async def underwash_boss(self, ctx):
        msg = """__**THE TRAITOR: JUDGE-23**__
:heart: : 12
:moneybag: : 1d19 :dagger:, 1d10 :gold:, 1d10 :test_tube:
Behavior: Summon another JUDGE-23 per :busts_in_silhouette:. Whenever a player gains an __effect__ this gains __Empower__
—————————————————
1-4   | **Heresy** (+1 :game_die:) :boom: targets random players. Repeats 2 times (w buffs applied).
5-7   | **Martyr** (-2 :game_die:) Cause __Weak__x2 to ALL players per damage taken. If this would have died this turn, all players gain __burn__x99 instead.
8-10 | **Doomsayer** If this took no damage, ALL players gain __Vulnerable__ at the start of every turn.
11+   | **Judgement** :boom::boom::boom::no_entry_sign: to ALL. If a player dies, repeat.
https://www.youtube.com/watch?v=bMfvZmhqW0A&pp=ygUTZ29kIHNoYXR0ZXJpbmcgc3Rhcg%3D%3D"""
        await ctx.send(msg)


if usingV2:
    async def setup(bot):
        cog = Wit(bot)
        await bot.add_cog(cog)
else:
    def setup(bot):
        bot.add_cog(Wit(bot))
