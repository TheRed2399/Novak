import discord
import asyncpraw
import random
from datetime import datetime
from discord.ext import commands

reddit = asyncpraw.Reddit(
                          client_id="JVQEPp37aajb5Q",
                          client_secret="-j1PXlcNrL5r8U4Pra9qiOS2152EYA",
                          password="",
                          user_agent="meme",
                          username="TheRed239")


class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(usage="meme")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def meme(self, ctx):
        subreddit = await reddit.subreddit("memes")
        all_subs = []

        hot = subreddit.hot(limit=50)

        async for submission in hot:
            all_subs.append(submission)

        post = random.choice(all_subs)

        embed = discord.Embed(title=post.title,
                              url=post.url,
                              color=discord.Color.random(),
                              timestamp=datetime.utcnow())
        embed.set_image(url=post.url)
        embed.set_footer(text="Created by cloudykid13#1006", icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))
