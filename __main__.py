import argparse
import sys
import time
from . import param, bot, git_manage, reloader

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config',
                    default=None,
                    type=str,
                    help='Load given config file.')
parser.add_argument('-t', '--token',
                    default=None,
                    type=str,
                    help='Use provided API token/file.')
parser.add_argument('-r', '--roasts',
                    default=None,
                    type=str,
                    help='Use provided roast file.')
args = parser.parse_args()

now = 0
while time.time() - now > 1:
    now = time.time()
    param.rc.read_config(args.config)
    token = param.rc.read_token(args.token)
    param.rc.read_roasts(args.roasts, add=False)
    tdt_bot = bot.MainBot()
    try:
        tdt_bot.run(token)
    except KeyboardInterrupt as e:
        raise e
    except RuntimeError as e:
        print(e)
    try:
        git_manage.update()
    except Exception as e:
        print(e)
    reloader.reload_package(sys.modules[__name__])
    reloader.reload_package(sys.modules[__name__])
    print("End of loop.")
