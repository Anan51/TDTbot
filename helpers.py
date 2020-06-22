from .param import rc as _rc


def find_channel(guild, name=None):
    """Find a channel in a guild based on its name"""
    if name is None:
        name = _rc('channel')
    try:
        return [i for i in guild.channels
                if i.name.lower().strip() == name.lower().strip()][0]
    except IndexError:
        return


def find_role(guild, name):
    """Find a role in a guild based on its name"""
    try:
        return [i for i in guild.roles if i.name.lower() == name.lower()][0]
    except IndexError:
        return
