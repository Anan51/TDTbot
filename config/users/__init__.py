import os
from ...param import DataContainer


_dir = os.path.split(os.path.realpath(__file__))[0]


class UserConfig(DataContainer):
    def __init__(self, discord_user, guild=None):
        fn = os.path.join(_dir, str(discord_user.id) + '.json')
        self.user = discord_user
        self.guild = guild
        super().__init__(fn)

    def _gen_data(self, *args):
        return
