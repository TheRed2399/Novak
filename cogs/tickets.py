import discord
import aiosqlite
import json
import chat_exporter
import io
from datetime import datetime
from discord.ext import commands


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def new(self, ctx, *, reason=None):
        db = await aiosqlite.connect("./tickets.db")

        with open('./config.json') as f:
            d = json.load(f)

        count = int(d["count"])
        count += 1

        channel = await ctx.guild.create_text_channel(f"ticket-{count}", topic=f"**Ticket Reason:** {reason}",
                                                      category=discord.utils.get(ctx.guild.categories, name="Tickets"))
        await channel.set_permissions(ctx.guild.default_role, read_messages=False, send_messages=False)
        await channel.set_permissions(ctx.author, read_messages=True, send_messages=True)

        embed = discord.Embed(title="Ticket Created",
                              description=f"You can access your ticket at {channel.mention}",
                              color=discord.Color.green(),
                              timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)

        embed2 = discord.Embed(title="New Ticket",
                               description=f"Hello, {ctx.author.mention}. please wait for support to assist you.",
                               color=discord.Color.green(),
                               timestamp=datetime.utcnow())
        embed2.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)

        cursor = await db.execute(
            f"CREATE TABLE IF NOT EXISTS [{channel.id}] ("
            "creator INTEGER PRIMARY KEY,"
            "treason TEXT"
            ");"
        )

        cursor2 = await db.execute(f'INSERT INTO [{channel.id}] (creator) VALUES (?)', (ctx.author.id,))
        cursor3 = await db.execute(f'INSERT INTO [{channel.id}] (treason) VALUES (?)', (reason,))
        d["count"] = int(count)
        with open("./config.json", 'w') as f:
            json.dump(d, f, indent=2)

        await ctx.send(embed=embed)
        await channel.send(embed=embed2)
        await db.commit()
        await cursor.close()
        await cursor2.close()
        await cursor3.close()

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def close(self, ctx, *, reason=None):
        db = await aiosqlite.connect("./tickets.db")
        try:
            await db.execute(f'SELECT * FROM [{ctx.channel.id}]')
        except aiosqlite.OperationalError:
            embed = discord.Embed(title="Ticket Does Not Exist", description="This channel is not a ticket.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        select_creator = await db.execute(f'SELECT creator FROM [{ctx.channel.id}]')
        creator = await select_creator.fetchone()
        creator = ''.join(map(str, creator))

        ticketc = await self.bot.fetch_user(creator)
        select_treason = await db.execute(f'SELECT treason FROM [{ctx.channel.id}]')
        treason = await select_treason.fetchone()
        treason = ''.join(map(str, treason))

        channel = discord.utils.get(ctx.guild.channels, name="log-spam")
        transcript = await chat_exporter.export(ctx.channel, set_timezone="US/Central")
        transcript = discord.File(io.BytesIO(transcript.encode()), filename=f"{ctx.channel.name}.html")
        transcript_log = await chat_exporter.export(ctx.channel, set_timezone="US/Central")
        transcript_log = discord.File(io.BytesIO(transcript_log.encode()), filename=f"{ctx.channel.name}.html")

        embed = discord.Embed(title="Ticket Resolved",
                              description=f"Your ticket has been resolved and closed by {ctx.author.mention}\nTicket Reason: {treason}\nClose Reason: {reason}",
                              color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)

        log = discord.Embed(title=":tickets: Ticket Logged",
                            description=f"**Ticket Name:** {ctx.channel.name}\n**Closed By:** {ctx.author.mention}\n**Ticket Reason:** {treason}\n**Close Reason:** {reason}",
                            color=discord.Color.green(), timestamp=datetime.utcnow())
        log.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)

        await ticketc.send(embed=embed, file=transcript)
        await channel.send(embed=log, file=transcript_log)
        await ctx.channel.delete()
        await db.commit()
        await select_creator.close()
        await select_treason.close()


def setup(bot):
    bot.add_cog(Tickets(bot))
