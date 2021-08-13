import discord
from discord.ext import commands
from datetime import datetime


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(usage="ping")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def ping(self, ctx):
        embed = discord.Embed(title="🏓 Ping Pong", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.add_field(name="WebSocket Latency:", value=f"{round(self.bot.latency * 1000)}ms", inline=False)
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(General(bot))
