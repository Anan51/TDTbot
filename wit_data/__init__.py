import random
import re
import os
import logging


logger = logging.getLogger('discord.' + __name__)

_wit_data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'wit_data'))
_remap = {'bosses': 'boss', 'encounters': 'encounter', 'enemies': 'enemy'}
_tmp = None


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
    # if '' in tasks:
    #    raise ValueError("Empty task")
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
        "**Spell Book** (-2 🔷): any effectx4",
        "**Wand** (-4 🔷): Double a target's active effect stacks",
        "**Runic Flintlock** (-1 🔷):💥; 1/6 chance to TRIPLE successful damage",
        "**Graven Shield** (-2 🔷): <:Sturdy:1152516154192044142> <:Persistence:1151788148322484234>🌀",
        "**Gilded Hammer** (-2 🔷): 💥🛡️🔀💥🌀 per success",
        "**Tome** (-4 🔷): Summon a Dire Wolf or an Automaton",
        "**Scroll** (-4 🔷): +2 🔷🌀",
        "**Enchanted Blade** (-4 🔷): 💥💥💥🌀",
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
        "**Splash Tincture of**: -Effect, +🌀",
        "**Splash Potion of**: +🌀",
        "**Splash Tonic of**: Roll Potion Effect list twice, -Effect, +🌀",
        "**Splash Elixir of**: +Effect, +🌀",
        "**Grand Splash Mixture of**: ++Effect, +🌀]",
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
        "**Safety Scissors**: ✂️ Once per run, you may escape an encounter or combat, go to the next level, but award no loot. May not be used on a boss ",
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


class WitData:
    _wit_cmds = dict()
    wit_cmd = make_decorator(_wit_cmds)

    def __init__(self, parent=None):
        self._data = dict()
        self._aliases = dict()
        self._active_commands = []
        self.parent = parent
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
                out = out()
        return out

    def set_command(self, cmd):
        """Set command in wit data files"""
        # if not cmd:
        #    raise ValueError("cmd must be a non-empty string")
        key = cmd[:]
        if self.parent:
            key = self.parent.set_command(cmd)
        self._active_commands.append(key)

    def load_data(self, overwrite=True):
        """Load wit data from files"""

        def path2dict(path, data=None):
            data = dict() if data is None else data
            for key in os.listdir(path):
                if key.endswith(".py") or key.startswith("."):
                    continue
                if key == '__pycache__':
                    continue
                if not key:
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
            tmp = {champ: ('random_champions', champ) for champ in self._data['random_champion']}
            safe_update(self._aliases, tmp)

            for key in self._data['tasks']:
                if key in self._aliases:
                    logger.warning(f"Collision between task and alias {key}")

        tmp = {k: (k,) for k in self._data.keys() if k not in ['zones', 'tasks']}
        safe_update(self._aliases, tmp)
        for cmd in self._wit_cmds:
            self.set_command(cmd)
        for cmd in self._data['tasks'].keys():
            self.set_command(cmd)
        for cmd in self._aliases.keys():
            self.set_command(cmd)
        return

    @wit_cmd
    def floor(self):
        options = ["💀 Enemy",
                   "☠️ Major",
                   "❔ Encounter",
                   "⛺ Camping Spot",
                   "🛖 Shop"
                   ]
        return ', '.join(random.choices(options, weights=[11, 2, 9, 1, 1], k=3))
