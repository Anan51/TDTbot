import discord
from discord.ext import commands
import logging
import os
import requests
import pytube
from urllib.parse import urlparse, parse_qs
from .. import param
from ..param import PermaDict
from ..helpers import *
from ..async_helpers import admin_check

logger = logging.getLogger('discord.' + __name__)
_dbm = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
_dbm = os.path.join(_dbm, 'config', 'content_videos.dbm')
_tdt_channel = "UCKBCsmU53MBzCm_wNZY7hLA"


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


# yt: https://pytube.io/en/latest/index.html
# twitter: https://realpython.com/twitter-bot-python-tweepy/
# psn: https://github_com.jam.dev/isFakeAccount/psnawp


class Content(commands.Cog):
    """Cog designed for debugging the bot"""

    def __init__(self, bot):
        self.bot = bot
        self.videos = PermaDict(_dbm)
        self._channel = None

    async def cog_check(self, ctx):
        """Don't allow everyone to access this cog"""
        return await admin_check(ctx)

    @property
    def channel(self):
        if self._channel is None:
            self._channel = self.bot.find_channel(param.rc('log_channel'))
        return self._channel

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
                    await self.channel.send('https://www.twitch.tv/tdt_ttv now streaming')
                continue
            yt_id = extract_video_id(i)
            if message.channel == self.channel:
                msg = f"yt:{yt_id} | url:{i}"
                await self.channel.send(msg)
            if yt_id:
                yt = pytube.YouTube(i)
                if message.channel == self.channel:
                    msg = f"yt_channel:{yt.channel_id}"
                    await self.channel.send(msg)
                if yt.channel_id == _tdt_channel:
                    await self.channel.send('watching ' + yt.url)
                continue


def setup(bot):
    bot.add_cog(Content(bot))
