import argparse
import sys
import time
import tracemalloc
from . import log_init
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
parser.add_argument('-v', '--verbose',
                    default=False,
                    action='store_true',
                    help="print all output, timestamps and logging information")
parser.add_argument('-l', '--logfile',
                    type=str,
                    default=None,
                    help='Set filename of logfile')
args = parser.parse_args()

now = 0
logger = log_init.logger
# while it takes more than 5 second to complete this loop
while time.time() - now > 5:
    now = time.time()
    # init param
    param.rc.read_config(args.config)
    token = param.rc.read_token(args.token)
    param.rc.read_roasts(args.roasts, add=False)
    kwargs = dict()
    kwargs.update(vars(args))
    kwargs.update(param.rc)
    log_init.init_logging(**kwargs)

    # init bot
    tdt_bot = bot.MainBot()
    try:
        # start bot loop
        tdt_bot.run(token)
    except KeyboardInterrupt as e:
        raise e
    except RuntimeError as e:
        logger.info(e)
    # if we get here, bot loop has ended
    try:
        # try to update own code via git
        git_manage.update()
    except Exception as e:
        logger.error(e)
    # reload all packages
    reloader.reload_package(sys.modules[__name__])
    reloader.reload_package(sys.modules[__name__])
    logger.printv("End of loop.")
