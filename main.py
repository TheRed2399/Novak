import discord
import os
import json
import random
import asyncio
from discord.ext import commands
import aiosqlite
from discord_components import DiscordComponents, Button, ButtonStyle
from datetime import datetime

with open("./config.json", "r") as f:
    config = json.load(f)

bot = commands.Bot(command_prefix=config['prefix'], owner_ids=(314166178144583682, 508111244260016131),
                   intents=discord.Intents.all(), allowed_mentions=discord.AllowedMentions.none(),
                   case_insensitive=True, help_command=None,
                   activity=discord.Activity(name=f"Novak / {config['prefix']}help",
                                             type=discord.ActivityType.listening))
os.environ['JISHAKU_NO_UNDERSCORE'] = 'True'
os.environ['JISHAKU_RETAIN'] = 'True'
os.environ['JISHAKU_HIDE'] = 'True'
os.environ['JISHAKU_NO_DM_TRACEBACK'] = 'True'

bot.load_extension("jishaku")


@bot.event
async def on_ready():
    DiscordComponents(bot)
    print(f"[ModBot] Bot is ready. Logged on as {bot.user}")


@bot.command(usage="help <command>")
@commands.cooldown(1, 3, commands.BucketType.user)
async def help(ctx, command=None):
    if command is None:
        def check(res):
            return res.user.id == ctx.author.id and res.channel.id == ctx.channel.id and res.message.id == msg.id

        embed = discord.Embed(title="ModBot's Help", description="Please select a help category.",
                              color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name)
        menu_components = [
            [
                Button(style=ButtonStyle.green, label="Fun"),
                Button(style=ButtonStyle.green, label="Music"),
                Button(style=ButtonStyle.green, label="Moderation"),
            ]
        ]
        msg = await ctx.send(embed=embed, components=menu_components)
        try:
            res = await bot.wait_for("button_click", check=check, timeout=30)
            if res.user.id != ctx.author.id:
                return
            if res.component.label == "Fun":
                cog = bot.get_cog('Fun').get_commands()
                commands = f'\n'.join([bot.command_prefix + c.name for c in cog])
                embed = discord.Embed(title="ModBot's Help",
                                      description=f"`{commands}`",
                                      color=discord.Color.green(),
                                      timestamp=datetime.utcnow())
                embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
                await res.respond(type=6)
                return await msg.edit(embed=embed, components=[])
            if res.component.label == "Music":
                cog = bot.get_cog('Music').get_commands()
                commands = f'\n'.join([bot.command_prefix + c.name for c in cog])
                embed = discord.Embed(title="ModBot's Help",
                                      description=f"`{commands}`",
                                      color=discord.Color.green(),
                                      timestamp=datetime.utcnow())
                embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
                await res.respond(type=6)
                return await msg.edit(embed=embed, components=[])
            if res.component.label == "Moderation":
                cog = bot.get_cog('Moderation').get_commands()
                commands = f'\n'.join([bot.command_prefix + c.name for c in cog])
                embed = discord.Embed(title="ModBot's Help",
                                      description=f"`{commands}`",
                                      color=discord.Color.green(),
                                      timestamp=datetime.utcnow())
                embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
                await res.respond(type=6)
                return await msg.edit(embed=embed, components=[])
        except asyncio.TimeoutError:
            timeout = discord.Embed(title="Timeout",
                                    description="No category was selected.",
                                    color=discord.Color.red(),
                                    timestamp=datetime.utcnow())
            timeout.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            await msg.delete()
            return await ctx.send(embed=timeout, delete_after=5)
        return

    try:
        command = bot.get_command(f"{command}")
        usage = command.usage
        alias = ', '.join(command.aliases)
        if command.usage is None:
            command.usage = "No command usage has been set"
        else:
            usage = f"{bot.command_prefix}{command.usage}"
        if not command.description:
            command.description = None
        if not command.aliases:
            alias = "No command aliases"

        embed = discord.Embed(title=f"{command.name}'s info",
                              description=f"**Name:** {command.name}\n**Description:** {command.description}\n**Usage:** {usage}\n**Aliases:** `{alias}`\n**Cooldown:** **{command.get_cooldown_retry_after(ctx):.0f}** seconds",
                              color=discord.Color.green(),
                              timestamp=datetime.utcnow())
        embed.set_footer(text="Created by cloudykid13#1006", icon_url=ctx.guild.icon_url)
        return await ctx.send(embed=embed)
    except AttributeError:
        embed = discord.Embed(title="Unknown Command",
                              description="I was unable to find a command with that name.",
                              color=discord.Color.red(),
                              timestamp=datetime.utcnow())
        embed.set_footer(text="Created by cloudykid13#1006", icon_url=ctx.guild.icon_url)
        return await ctx.send(embed=embed)


@bot.command()
async def dm(ctx, user: discord.User, *, text: str):
    user = await bot.fetch_user(user.id)
    await user.send(text)


@bot.command(name="8ball", usage="8ball <question>")
@commands.cooldown(1, 3, commands.BucketType.user)
async def eightball(ctx, *, question):
    answer = ["It is certain",
              "It is decidedly so",
              "Without a doubt",
              "Yes, definitely",
              "You may rely on it",
              "As I see it, yes",
              "Most likely",
              "Outlook good",
              "Yes",
              "Signs point to yes",
              "Reply hazy try again",
              "Ask again later",
              "Better not tell you now",
              "Cannot predict now",
              "Concentrate and ask again",
              "Don't count on it",
              "My reply is no",
              "My sources say no",
              "Outlook not so good",
              "Very doubtful"]

    answer = random.choice(answer)
    embed = discord.Embed(title="Magic 8Ball",
                          description=f"Question: {question}\nAnswer: {answer}",
                          color=discord.Color.random(),
                          timestamp=datetime.utcnow())
    embed.set_thumbnail(url=ctx.author.avatar_url)
    embed.set_footer(text="Created by cloudykid13#1006", icon_url=ctx.guild.icon_url)
    await ctx.send(embed=embed)


for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")

try:
    bot.run(config['token'])
except discord.errors.LoginFailure:
    print("Invalid token")
