import discord
import wavelink
import json
from discord.ext import commands
from datetime import datetime

with open("./config.json", "r") as f:
    config = json.load(f)


class errorHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.NotOwner):
            return

        if isinstance(error, commands.MissingRole):
            embed = discord.Embed(title="No Required Roles",
                                  description=f"**{error.missing_role}** is required to use this command.",
                                  color=discord.Color.red(),
                                  timestamp=datetime.utcnow())
            embed.set_footer(text="Created by cloudykid13#1006", icon_url=ctx.guild.icon_url)
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.CommandInvokeError):
            embed = discord.Embed(title="Bot Error",
                                  description=f"A bot error has occurred.\n```py\n{type(error.original)}: {error.original}```",
                                  color=discord.Color.red(),
                                  timestamp=datetime.utcnow())
            embed.set_footer(text="Created by cloudykid13#1006", icon_url=ctx.guild.icon_url)
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.MissingRequiredArgument):
            command = self.bot.get_command(f"{ctx.command}")
            if command.usage is None or command.usage == "No command usage has been set":
                embed = discord.Embed(title="No Required Arguments",
                                    description="**A command usage has not been set for this command.**",
                                    color=discord.Color.red(),
                                    timestamp=datetime.utcnow())
                embed.set_footer(text="Created by cloudykid13#1006", icon_url=ctx.guild.icon_url)
                return await ctx.send(embed=embed)

            else:
                embed = discord.Embed(title="No Required Arguments",
                                    description=f"**{self.bot.command_prefix}{command.usage}**",
                                    color=discord.Color.red(),
                                    timestamp=datetime.utcnow())
                embed.set_footer(text="Created by cloudykid13#1006", icon_url=ctx.guild.icon_url)
                await ctx.send(embed=embed)
                return

        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(title="Command Cooldown",
                                  description=f"You are currently in cooldown for **{error.retry_after:.0f}** seconds",
                                  color=discord.Color.red(),
                                  timestamp=datetime.utcnow())
            embed.set_footer(text="Created by cloudykid13#1006", icon_url=ctx.guild.icon_url)
            await ctx.send(embed=embed)
            return


def setup(bot):
    bot.add_cog(errorHandler(bot))
