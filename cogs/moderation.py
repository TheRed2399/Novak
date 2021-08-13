import discord
import chat_exporter
from io import BytesIO
from discord.ext import commands
from datetime import datetime
from discord_components import DiscordComponents, Button, ButtonStyle, InteractionType


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(usage="purge <amount>", aliases=["clear"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def purge(self, ctx, amount: int):
        embed = discord.Embed(title="Messages Cleared",
                              description=f"**{amount}** messages have been cleared.",
                              color=discord.Color.green(),
                              timestamp=datetime.utcnow())
        embed.set_footer(text="Created by cloudykid13#1006", icon_url=ctx.guild.icon_url)
        message = await ctx.message.delete()
        messages = await ctx.channel.purge(limit=amount)
        await ctx.send(embed=embed, delete_after=3)

        transcript = await chat_exporter.raw_export(ctx.channel, messages, set_timezone="US/Central")
        channel = discord.utils.get(ctx.guild.channels, name="log-spam")

        if transcript is None:
            return

        transcript_file = discord.File(BytesIO(transcript.encode()),
                                filename=f"messages-{ctx.channel.name}.html")

        embed = discord.Embed(title="💬 Messages Purged",
                              description=f"**{len(messages)}** purged messages have been logged.",
                              color=discord.Color.green(),
                              timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await channel.send(embed=embed, file=transcript_file)

    @commands.command(usage="ban <user> [reason]")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def ban(self, ctx, user: discord.User, reason=None):
        try:
            embed = discord.Embed(title="User Banned",
                                description=f"{user.mention} has been successfully banned.",
                                color=discord.Color.green(),
                                timestamp=datetime.utcnow())
            embed.set_footer(text="Created by cloudykid13#1006", icon_url=ctx.guild.icon_url)
            await ctx.guild.ban(user=user, reason=reason)
            await ctx.send(embed=embed)
        except discord.errors.Forbidden:
            embed = discord.Embed(title="User Not Bannable",
                                description=f"{user.mention} cannot be banned.",
                                color=discord.Color.red(),
                                timestamp=datetime.utcnow())
            embed.set_footer(text="Created by cloudykid13#1006", icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

    @commands.command(usage="unban <user>")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def unban(self, ctx, user: discord.User, *, reason=None):
        if reason is None:
            reason = None
        try:
            embed = discord.Embed(title="User Unbanned",
                                description=f"{user.mention} has been successfully unbanned.",
                                color=discord.Color.green(),
                                timestamp=datetime.utcnow())
            embed.set_footer(text="Created by cloudykid13#1006", icon_url=ctx.guild.icon_url)
            await ctx.guild.unban(user=user, reason=reason)
            await ctx.send(embed=embed)
        except discord.NotFound:
            embed = discord.Embed(title="User Not Banned",
                                description=f"{user.mention} is not banned.",
                                color=discord.Color.red(),
                                timestamp=datetime.utcnow())
            embed.set_footer(text="Created by cloudykid13#1006", icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.content == after.content:
            return

        if before.author.bot:
            return

        channel = discord.utils.get(before.guild.channels, name="log-spam")

        embed = discord.Embed(title=f"💬 Message Edited | {before.channel}",
                              description=f"**Old Message:** {before.content}\n**New Message:** {after.content}",
                              color=discord.Color.green(),
                              timestamp=datetime.utcnow())
        embed.set_author(name=f"{before.author}", icon_url=before.author.avatar_url)
        embed.set_footer(text=before.guild.name, icon_url=before.guild.icon_url)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        channel = discord.utils.get(message.guild.channels, name="log-spam")

        embed = discord.Embed(title=f"💬 Message Deleted | {message.channel}",
                              description=f"**Message:** {message.content}",
                              color=discord.Color.green(),
                              timestamp=datetime.utcnow())
        embed.set_author(name=f"{message.author}", icon_url=message.author.avatar_url)
        embed.set_footer(text=message.guild.name, icon_url=message.guild.icon_url)
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Moderation(bot))
