import discord  # type: ignore
from discord.ext import commands  # type: ignore
import asyncio
import logging
import os
from .. import param, users
from ..config import UserConfig
from ..helpers import find_role
from ..async_helpers import admin_check, parse_payload, split_send


logger = logging.getLogger('discord.' + __name__)

_dbm = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
_dbm = os.path.join(_dbm, 'config', 'direct_messages.dbm')


class DirectMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        self._kicks = {}
        self._configs = {}
        self._channel = None
        self.data = param.IntPermaDict(_dbm)
        self._init = False
        self._init_finished = False
        self._chancla = None

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(5)
        await self._async_init()

    async def _async_init(self):
        if self._init:
            return
        self._init = True
        guild = self.bot.tdt()
        try:
            self._chancla = [e for e in guild.emojis if e.name == "Chancla"][0]
        except IndexError:
            pass
        self._init_finished = True

    @property
    def chancla(self):
        return self._chancla

    async def cog_check(self, ctx):
        """Don't allow everyone to access this cog"""
        await self._async_init()
        if not await admin_check(ctx):
            return False
        return ctx.channel == self.channel

    def _get_config(self, user=None):
        """Get a user's config file"""
        if user is None:
            user = self.bot.user
        try:
            return self._configs[user.id]
        except KeyError:
            self._configs[user.id] = UserConfig(user)
            return self._configs[user.id]

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

    @commands.command()
    async def send_dm(self, ctx, target: discord.User, *args):
        """<user> <message> sends a direct message to a user"""
        msg = " ".join(args)
        channel = target.dm_channel
        if channel is None:
            channel = await target.create_dm()
        await split_send(channel, msg)

    @commands.command()
    async def dm_data(self, ctx):
        """Prints the direct message data"""
        lines = ["{}: {}".format(i, self[i]) for i in self.keys()]
        await split_send(ctx, lines, style='```')

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for DMs and post them in the bot log channel"""
        await self._async_init()
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
            # roles = [find_role(channel.guild, i).name for i in ["admin", "devoted"]]
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
                        # check for discord links in message
                        if "https://discord.gg" in message.content:
                            emojis = [self.chancla if self.chancla else '👟', '⬅️', '❓']
                            for emoji in emojis:
                                await message.add_reaction(emoji)
                                await asyncio.sleep(.1)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle emoji reactions to DMs"""
        await self._async_init()
        # if bot
        if payload.user_id == self.bot.user.id:
            return
        if payload.user_id == users.stellar:
            print(payload)
        # if message is from a DM
        if payload.message_id in self:
            data = await parse_payload(payload, self.bot, "guid", "member")
            member, guild = data["member"], data["guild"]
            emoji = payload.emoji.name.lower()
            print(payload.emoji, payload.emoji.name)
            print(payload)
            # if reaction is a kick
            if "foot" in emoji or "shoe" in emoji or "chancla" in emoji or emoji in ["👟", "🦶", "👞"]:
                # if emoji poster is admin or devoted
                if await admin_check(bot=self.bot, author=member, guild=guild):
                    channel = await self.bot.fetch_channel(self[payload.message_id])
                    recipient = channel.recipient
                    msg = "Are you sure you want to kick {}?".format(recipient)
                    msg = await self.channel.send(msg)
                    await msg.add_reaction('✅')
                    await msg.add_reaction('❌')
                    self._kicks[msg.id] = recipient.id
        # if reacting to a kick prompt
        elif payload.message_id in self._kicks:
            data = await parse_payload(payload, self.bot, "guid", "member")
            member, guild = data["member"], data["guild"]
            # if emoji poster is admin or devoted
            if await admin_check(bot=self.bot, author=member, guild=guild):
                if payload.emoji.name == '✅':
                    member = await self.bot.get_or_fetch_user(self._kicks[payload.message_id], guild=guild)
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
