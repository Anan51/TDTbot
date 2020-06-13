import argparse
import sys
from . import param, bot, git, reloader

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config',
                    default=None,
                    type=str,
                    help='Load given config file.')
parser.add_argument('-t', '--token',
                    default=None,
                    type=str,
                    help='Use provided API token/file.')
args = parser.parse_args()


while True:
    param.rc.read_config(args.config)
    param.rc.read_token(args.token)
    try:
        bot.run()
    except KeyboardInterrupt as e:
        raise e
    except git.ExitForGitUpdate:
        git.update()
        reloader.reload_package(sys.modules[__name__])
        reloader.reload_package(sys.modules[__name__])
