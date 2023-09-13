import discord  # type: ignore # noqa: F401
from discord.ext import commands  # type: ignore
import asyncio
import datetime
import random
import re
import os
from .. import param
from ..config import UserConfig
from ..version import usingV2
from ..async_helpers import split_send, sleep
from ..helpers import second, minute, localize
import logging
import traceback
from inspect import iscoroutinefunction


logger = logging.getLogger('discord.' + __name__)


_channel_id = param.channels.champions_landing
_wit_data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'wit_data'))
_remap = {'bosses': 'boss', 'encounters': 'encounter', 'enemies': 'enemy'}
_wit_prefix = "wit$"


# keywords for player/bot config storage
_bot_key = "tdt.wit"
_msg_key = _bot_key + ".msg"


def parse_encounter(txt):
    import re
    out = dict()
    txt = txt.strip()
    chunks = re.split(r"\n-{3,}", txt)
    lines = chunks[0].split('\n')
    out['title'] = lines[0].strip().strip('_*').lower()
    out['body'] = ('\n'.join(lines)).strip()
    tasks = {}
    for chunk in chunks[1:]:
        chunk = chunk.strip()
        match = re.search(r"tdt\$(?P<task>.*)", chunk)
        tasks[match['task']] = chunk[match.end():].strip()
    out['tasks'] = tasks
    if not tasks:
        return out['body']
    return out


def safe_update(d, u, key=None):
    if key is not None:
        u = {key: u}
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = safe_update(d.get(k, {}), v)
        else:
            if k in d:
                if d[k] != v:
                    logger.warning(f"Overwriting {k} with {v}")
            d[k] = v
    return d


async def safe_send(channel, message):
    if len(message) < 2000:
        await channel.send(message)
    else:
        tmp = re.split(r"(\.+)", message)
        if not tmp:
            return
        out = [tmp[0]]
        for s in tmp[1:]:
            if s.startswith('.'):
                out[-1] += s
            else:
                out.append(s)
        chunks = [out[0]]
        for s in out[1:]:
            if len(chunks[-1]) + len(s) < 2000:
                chunks[-1] += s
            else:
                chunks.append(s)
        for s in chunks:
            await channel.send(s)


def make_decorator(dct):
    # *This* will be the function bound to the name 'wit_cmd'
    _tmp = None

    def _(meth=None, *, aliases=None):
        global _tmp
        if meth is None:
            _tmp = aliases
            return _
        if _tmp is not None:
            aliases = _tmp
            _tmp = None
        if aliases is None:
            aliases = []
        if isinstance(aliases, str):
            aliases = [aliases]
        dct[meth.__name__] = meth
        for i in aliases:
            dct[i] = meth
        return meth
    return _


# time between major wit events
def random_time(nlast=3, add_random=True):
    """Return a random time in seconds. Taken from trick_or_treat.py.
    nlast is the number of votes last time. Times are in seconds."""
    if nlast is None:
        nlast = 5
    if add_random:
        nlast += random.uniform(-1, 1)
    nlast = min(max(1, nlast), 10)
    shape = 22 - 2 * nlast
    scale = -1.4 * nlast + 16.4
    ratio = 5 * (16 - nlast) * 7
    t = (random.weibullvariate(shape, scale) + .5) * ratio
    return min(max(3600, t), 3*3600) * 9999999


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


class Wit2(commands.Cog, command_attrs=dict(hidden=True)):
    _wit_cmds = dict()
    wit_cmd = make_decorator(_wit_cmds)

    def __init__(self, bot):
        self.bot = bot
        self._init = False
        self._init_finished = False
        self._gold = None
        self._active_message_id = None
        self._dt = 60 * minute
        self._channel = None
        self._configs = dict()
        self._data = dict()
        self._aliases = dict()
        self._active_commands = []
        self.load_data()

    def get_data(self, *keys):
        """Retrieve preloaded wit data"""
        data = self._data
        for key in keys:
            data = data[key]
        return data

    def get_command(self, cmd, exicute=True):
        """Get command from wit data files"""
        if cmd in self._wit_cmds:
            out = getattr(self, cmd)
        else:
            try:
                out = self._data['tasks'][cmd]
            except KeyError:
                out = self.get_data(*self._aliases[cmd])
        if exicute:
            while isinstance(out, dict):
                out = random.choice(list(out.values()))
            while callable(out):
                if iscoroutinefunction(out):
                    return out
                else:
                    out = out()
        return out

    def set_command(self, cmd):
        """Set command in wit data files"""
        async def _(self, ctx, *args):
            await ctx.send(self.get_command(cmd))

        func = commands.command(name=cmd)(_)
        setattr(self, cmd, func)
        self._active_commands.append(cmd)

    async def _async_init(self):
        if self._init:
            return
        self._init = True
        self._channel = await self.bot.fetch_channel(_channel_id)
        guild = self.bot.tdt()
        try:
            self._gold = [e for e in guild.emojis if e.name == "gold"][0]
        except IndexError:
            pass
        await self.send_major()
        self._init_finished = True

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(5)
        await self._async_init()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Parse messages"""
        try:
            # ignore all messages from our bot
            if message.author == self.bot.user:
                return
            await self._async_init()
            # ignore normal commands
            try:
                if message.content.startswith(self.bot.command_prefix):
                    return
            except TypeError:
                for prefix in self.bot.command_prefix:
                    if message.content.startswith(prefix):
                        return
            if not message.content.lower().startswith(_wit_prefix):
                return
            if message.channel.category_id != param.channels.wit_category:
                return
            words = message.content[len(_wit_prefix):].strip().split(' ')
            cmd = words[0].lower()
            cmd = self.get_command(cmd)
            if iscoroutinefunction(cmd):
                cmd = await cmd(message.channel, *words[1:])
                if cmd is None:
                    return
            await safe_send(message.channel, cmd)
        except Exception as e:
            logger.error(e)
            tb = traceback.format_exc()
            logger.error(tb)
            channel = await self.bot.fetch_channel(param.channels.debugging)
            await channel.send("Wit issue:")
            await channel.send(e)
            await channel.send(f"```{tb}```")

    def _get_config(self, user=None):
        """Get a user's config file"""
        if user is None:
            user = self.bot.user
        try:
            return self._configs[user.id]
        except KeyError:
            self._configs[user.id] = UserConfig(user)
            return self._configs[user.id]

    def load_data(self, overwrite=True):
        """Load wit data from files"""

        def path2dict(path, data=None):
            data = dict() if data is None else data
            for key in os.listdir(path):
                if key.endswith(".py") or key.startswith("."):
                    continue
                fn = os.path.join(path, key)
                if os.path.isfile(fn):
                    key = os.path.splitext(key)[0]
                    with open(fn, 'r') as f:
                        info = parse_encounter(f.read())
                        if isinstance(info, dict):
                            data[key] = info['body']
                            safe_update(self._data, info['tasks'], 'tasks')
                        else:
                            data[key] = info
                elif os.path.isdir(fn):
                    data[key] = path2dict(fn)
                else:
                    logger.warning(f"Unknown file type: {fn}")
            return data

        if overwrite or not self._data:
            for cmd in self._active_commands:
                delattr(self, cmd)
            self._active_commands = []
            self._data = dict()
            self._data = path2dict(_wit_data_path, data=self._data)

            self._aliases = dict()
            for zone in self._data['zones']:
                for key in self._data['zones'][zone]:
                    if key == "additional_commands":
                        tmp = {k: ('zones', zone, key, k) for k in self._data['zones'][zone][key]}
                    else:
                        tmp = {zone + "_" + _remap.get(key, key): ('zones', zone, key)}
                    safe_update(self._aliases, tmp)

            for key in self._data['tasks']:
                if key in self._aliases:
                    logger.warning(f"Collision between task and alias {key}")

    @property
    def message_id(self):
        """Active trick-or-treat game message id"""
        if self._active_message_id is None:
            try:
                self._active_message_id = self._get_config().set_if_not_set(_msg_key, 0)
            except AttributeError:
                self._active_message_id = None
        return self._active_message_id

    async def message_active(self):
        if not self.message_id:
            return False
        msg = await self._get_message()
        if localize(msg.created_at) < localize(datetime.datetime.utcnow() - self._dt):
            self._set_msg_id(0)
            return False
        return True

    @property
    def channel(self):
        if self._channel is None:
            self._channel = self.bot.find_channel(_channel_id)
        return self._channel

    async def send_major(self, dt=0, set_timer=True):
        """Send wit major"""
        # if we have an active game message already then quit
        if not dt and await self.message_active():
            return
        if dt is True:
            dt = random_time()
            self._dt = dt * second
        await sleep(dt)
        # ensure some funny business didn't happen while we were waiting
        if await self.message_active():
            return
        # send new active game message
        enemies = self.get_data('zones', 'champions_landing', 'enemies')
        msg = "# MAJOR\n" + random.choice(enemies)
        msg = await self.channel.send(msg)
        self._set_msg_id(msg.id)
        if set_timer is not True and set_timer < .01:
            set_timer = .01
        if set_timer:
            # launch task for delayed message
            self.bot.loop.create_task(self.send_major(dt=set_timer))

    async def _get_message(self):
        """Get active game message id"""
        if self.message_id:
            try:
                return await self.channel.fetch_message(self.message_id)
            except discord.NotFound:
                self._set_msg_id(0)

    def _set_msg_id(self, idn):
        """set active message id and return old one"""
        old = self.message_id
        self._active_message_id = idn
        self._get_config(self.bot.user)[_msg_key] = idn
        return old

    @property
    def gold(self):
        return self._gold if self._gold else "<:gold:1058304371940655185>"

    # @commands.command()
    @wit_cmd()
    async def wit_shop(self, ctx):
        await split_send(ctx, gen_shop(), "\n\n")

    # @commands.command(aliases=['r'])
    @wit_cmd(aliases=['r'])
    async def roll(self, ctx, roll_str):
        rolls = roll(roll_str)
        msg = ' + '.join([str(i) for i in rolls])
        if len(rolls) > 1:
            msg += ' = {:}'.format(sum(rolls))
        await ctx.send(msg)

    # @commands.command()
    @wit_cmd()
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
        cog = Wit2(bot)
        await bot.add_cog(cog)
else:
    def setup(bot):
        bot.add_cog(Wit2(bot))
