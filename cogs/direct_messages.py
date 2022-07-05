import datetime
import discord
from discord.ext import commands
import logging
from .. import param, users
from ..config import UserConfig
from ..helpers import *
from ..async_helpers import *


logger = logging.getLogger('discord.' + __name__)

_bot = "tdt.dms"


class DirectMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self._kicks = {}
        self._configs = {}
        self._channel = None

    def _get_config(self, user=None):
        """Get a user's config file"""
        if user is None:
            user = self.bot.user
        try:
            return self._configs[user.id]
        except KeyError:
            self._configs[user.id] = UserConfig(user)
            return self._configs[user.id]

    @property
    def data(self):
        """Get the data file for the bot"""
        try:
            return self._get_config()[_bot]
        except KeyError:
            self._get_config()[_bot] = {}
            return self._get_config()[_bot]

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, item):
        return item in self.data

    def keys(self):
        return self.data.keys()

    @property
    def channel(self):
        """Get the log channel for the bot"""
        if self._channel is None:
            self._channel = self.bot.find_channel(param.rc('log_channel'))
        return self._channel

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for DMs and post them in the bot log channel"""
        # ignore messages from this bot
        if message.author == self.bot.user:
            return
        # ignore commands
        try:
            if message.content.startswith(self.bot.command_prefix):
                return
        except TypeError:
            for prefix in self.bot.command_prefix:
                if message.content.startswith(prefix):
                    return
        # if DM
        if type(message.channel) == discord.DMChannel:
            channel = self.bot.find_channel(param.rc('log_channel'))
            roles = [find_role(channel.guild, i).mention for i in ["admin", "devoted"]]
            msg = ' '.join(roles) + '\n'
            msg += 'From: {0.author}\n"{0.content}"'.format(message)
            sent = [await channel.send(msg)]
            urls = []
            if message.attachments:
                msg = '\nAttachments:\n'
                msg += '```\n{}\n```'.format(message.attachments)
                for attachment in message.attachments:
                    if attachment.url and attachment.url not in urls:
                        urls.append(attachment.url)
                sent.append(await channel.send(msg))
            if urls:
                sent.extend(await split_send(channel, urls))
            for i in sent:
                self[i.id] = message.channel.id
            return
        # if message from log channel
        if message.channel == self.channel:
            if await admin_check(bot=self.bot, author=message.author, guild=self.channel.guild):
                # if message is reply to a previous message
                if message.reference:
                    if message.reference.message_id in self:
                        channel = self.bot.get_channel(self[message.reference.message_id])
                        await channel.send(message.content)
                        await message.add_reaction('✅')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle emoji reactions to DMs"""
        # if bot
        if payload.user_id == self.bot.user.id:
            return
        # if message is from a DM
        if payload.message_id in self:
            data = parse_payload(payload, self.bot, "guid", "member")
            member, guild = data["member"], data["guild"]
            emoji = payload.emoji.name.lower()
            # if reaction is a kick
            if "foot" in emoji or "shoe" in emoji:
                # if emoji poster is admin or devoted
                if await admin_check(bot=self.bot, author=member, guild=self.channel.guild):
                    channel = await self.bot.fetch_channel(self[payload.message_id])
                    recipient = channel.recipient
                    msg = "Are you sure you want to kick {}?".format(recipient)
                    msg = await self.channel.send(msg)
                    await msg.add_reaction('✅')
                    await msg.add_reaction('❌')
                    self._kicks[msg.id] = recipient.id
        # if reacting to a kick prompt
        elif payload.message_id in self._kicks:
            data = parse_payload(payload, self.bot, "guid", "member")
            member, guild = data["member"], data["guild"]
            # if emoji poster is admin or devoted
            if await admin_check(bot=self.bot, author=member, guild=self.channel.guild):
                if payload.emoji.name == '✅':
                    member = await self.bot.get_or_fetch_user(self._kicks[payload.message_id])
                    await member.kick()
                    await self.channel.send("{} has been kicked".format(member))
                    del self._kicks[payload.message_id]
                elif payload.emoji.name == '❌':
                    member = await self.bot.get_or_fetch_user(self._kicks[payload.message_id])
                    await self.channel.send("Cancelled kick of {}".format(member))
                    del self._kicks[payload.message_id]


def setup(bot):
    """This is required to add this cog to a bot as an extension"""
    bot.add_cog(DirectMessages(bot))
