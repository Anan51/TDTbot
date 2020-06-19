from .param import rc as _rc


def find_channel(guild, name=None):
    if name is None:
        name = _rc('channel')
    return [i for i in guild.channels if i.name.lower() == name.lower()][0]


def find_role(guild, name):
    return [i for i in guild.roles if i.name.lower() == name.lower()][0]
