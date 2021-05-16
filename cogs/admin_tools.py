import discord
from discord.ext import commands
import logging
from ..helpers import *
from ..async_helpers import admin_check, git_log, split_send
from .. import git_manage


logger = logging.getLogger('discord.' + __name__)


class AdminTools(commands.Cog):
    """Cog designed for debugging the bot"""
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Don't allow everyone to access this cog"""
        return await admin_check(ctx)

    @commands.command()
    async def clear_rxn(self, ctx, emote: str, msg_id: int = None,
                        channel: discord.abc.Messageable = None):
        """<emote> <message id (optional)> <channel (optional)>
        Clear all of the specified reaction for the message

        Can be used as a reply to a message, in this case:
        <message id> defaults to the message that's being replied to.
        <channel> defaults to the channel where this command was entered."""

        ref = ctx.message.reference
        try:
            emote = int(emote)
        except ValueError:
            pass
        if channel is None:
            channel = ctx.channel
        msg = None
        if msg_id is not None:
            msg = await channel.fetch_message(msg_id)
        if msg is None and msg_id is None and ref:
            if hasattr(ref, 'resolved'):
                msg = ref.resolved
            else:
                channel = self.bot.find_channel(ref.channel_id)
                if channel is None:
                    channel = await self.bot.fetch_channel(ref.channel_id)
                if channel is None:
                    msg = ref
                else:
                    msg = await channel.fetch_message(ref.message_id)
        if not msg:
            raise ValueError("Cannot identify message.")
        rxns = [rxn for rxn in msg.reactions if emotes_equal(emote, rxn.emoji)]
        if rxns:
            await rxns[0].clear()

    @commands.command()
    async def reboot(self, ctx):
        """Reboots this bot"""
        await ctx.send("Ok. I will reboot now.")
        logger.printv('\nRebooting\n\n\n\n')
        # This exits the bot loop, allowing __main__ loop to take over
        await self.bot.loop.run_until_complete(await self.bot.logout())

    @commands.command()
    async def speak(self, ctx, message, channel: discord.TextChannel = None, guild: str = None):
        """Speak as the bot"""
        if guild is None:
            guild = ctx.guild
        else:
            try:
                guild = [i for i in self.bot.guilds if i.name == guild][0]
            except IndexError:
                ctx.send('ERROR: server "{0}" not found.'.format(guild))
                return
        if channel:
            channel = find_channel(guild, channel)
        else:
            channel = ctx.channel
        await channel.send(message)


def setup(bot):
    bot.add_cog(AdminTools(bot))
