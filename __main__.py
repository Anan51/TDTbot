import argparse
import sys
import time
import tracemalloc
from . import param, bot, git_manage, reloader

# for traceback info to debug
tracemalloc.start()

# setup and parse command line options
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
# while it takes more than 5 second to complete this loop
while time.time() - now > 5:
    now = time.time()
    # init param
    param.rc.read_config(args.config)
    token = param.rc.read_token(args.token)
    param.rc.read_roasts(args.roasts, add=False)
    # init bot
    tdt_bot = bot.MainBot()
    try:
        # start bot loop
        tdt_bot.run(token)
    except KeyboardInterrupt as e:
        raise e
    except RuntimeError as e:
        print(e)
    # if we get here, bot loop has ended
    try:
        # try to update own code via git
        git_manage.update()
    except Exception as e:
        print(e)
    # reload all packages
    reloader.reload_package(sys.modules[__name__])
    reloader.reload_package(sys.modules[__name__])
    print("End of loop.")
