import discord
from discord.ext import commands
import datetime
import logging
import os
import requests
from urllib import request
from urllib.parse import urlparse, parse_qs
from .. import param
from ..param import PermaDict
from ..helpers import *
from ..async_helpers import admin_check, split_send
from ..twitter import tweet

logger = logging.getLogger('discord.' + __name__)
_dbm = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
_dbm = os.path.join(_dbm, 'config', 'content_videos.dbm')
_tdt_channel = "UCKBCsmU53MBzCm_wNZY7hLA"
_channel_tag = '<meta itemprop="channelId" content="{}">'.format(_tdt_channel)
_month = 30*24*60*60
_ttv_cooldown = datetime.timedelta(minutes=5)


# https://stackoverflow.com/a/67969583/2275975
def ttv_streaming(channel='tdt_ttv'):
    contents = requests.get('https://www.twitch.tv/' + channel).content.decode('utf-8')
    return 'isLiveBroadcast' in contents


# https://stackoverflow.com/a/54383711/2275975
# noinspection PyTypeChecker
def extract_video_id(url):
    # Examples:
    # - http://youtu.be/SA2iWivDJiE
    # - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    # - http://www.youtube.com/embed/SA2iWivDJiE
    # - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    query = urlparse(url)
    if query.hostname == 'youtu.be': return query.path[1:]
    if query.hostname in {'www.youtube.com', 'youtube.com'}:
        if query.path == '/watch': return parse_qs(query.query)['v'][0]
        if query.path[:7] == '/watch/': return query.path.split('/')[1]
        if query.path[:7] == '/embed/': return query.path.split('/')[2]
        if query.path[:3] == '/v/': return query.path.split('/')[2]
        # below is optional for playlists
        if query.path[:9] == '/playlist': return parse_qs(query.query)['list'][0]
    # returns None for invalid YouTube url


# twitter: https://realpython.com/twitter-bot-python-tweepy/
# psn: https://github_com.jam.dev/isFakeAccount/psnawp


class Content(commands.Cog):
    """Cog designed for debugging the bot"""

    def __init__(self, bot):
        self.bot = bot
        self.videos = PermaDict(_dbm)
        self._channel = None
        self._ttv_cooldown = None

    async def cog_check(self, ctx):
        """Don't allow everyone to access this cog"""
        return await admin_check(ctx)

    @property
    def channel(self):
        if self._channel is None:
            self._channel = self.bot.find_channel(param.rc('log_channel'))
        return self._channel

    def _add_yt_id(self, yt_id):
        """Add YouTube ID to video is not already there and clear old videos"""
        if yt_id in self.videos:
            return False
        now = int_time(datetime.datetime.utcnow())
        self.videos[yt_id] = now
        del_list = [i for i in self.videos if self.videos[i] < now - _month]
        for i in del_list:
            self.videos.pop(i)
        return True

    @commands.Cog.listener()
    async def on_message(self, message):
        """Parse messages for new memes and add reactions"""
        # ignore commands
        try:
            if message.content.startswith(self.bot.command_prefix):
                return
        except TypeError:
            for prefix in self.bot.command_prefix:
                if message.content.startswith(prefix):
                    return
        # ignore messages from this bot
        if message.author == self.bot.user:
            return
        data = parse_message(message)
        for i in data['urls']:
            i = i.rstrip('/')
            # if twitch url is streaming
            if i == 'https://www.twitch.tv/tdt_ttv':
                if ttv_streaming():
                    now = datetime.datetime.utcnow()
                    if self._ttv_cooldown is not None:
                        if self._ttv_cooldown > now:
                            continue
                    await self.channel.send('https://www.twitch.tv/tdt_ttv now streaming')
                    tweet(i)
                    self._ttv_cooldown = now + _ttv_cooldown
                continue
            yt_id = extract_video_id(i)
            if yt_id:
                logger.printv('yt: {} {}'.format(i, yt_id))
                tdt_channel = False
                with request.urlopen(i) as response:
                    # set the correct charset below
                    tdt_channel = _channel_tag in response.read().decode('utf-8')
                logger.printv('yt channel: {}'.format(tdt_channel))
                if tdt_channel:
                    if self._add_yt_id(yt_id):
                        await self.channel.send('watching ' + i)
                        tweet(i)
                continue

    @commands.command()
    async def clear_yt_data(self, ctx):
        keys = self.videos.keys()
        for key in keys:
            self.videos.delete(key)

    @commands.command()
    async def print_yt_data(self, ctx):
        lines = ["{}: {}".format(*i) for i in self.videos.items()]
        await split_send(ctx, lines, style='```')


def setup(bot):
    bot.add_cog(Content(bot))
