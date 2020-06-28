# TDTbot
A Discord bot for The Dream Team clan

### Dependancies
1) Python >= 3.5.3
2) discordpy https://discordpy.readthedocs.io/en/latest/intro.html#installing
3) gitpython https://gitpython.readthedocs.io/en/stable/intro.html
4) pytz (installable with `conda` or `pip`)

### Install
In the `config` subdirectory create a file `token.txt` with your bot's token in it. See https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token for help on bot tokens.

### Usage
- Run: `python3 -m TDTbot <optional flags>`
- Help/see options: `python3 -m TDTbot -h`

### Configuration
The default config file is `config/tdt.json`, defaults can be found near the top of `param.py`.