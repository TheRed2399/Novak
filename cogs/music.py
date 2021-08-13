import discord
import wavelink
import asyncio
import async_timeout
import time
import subprocess
from datetime import datetime, timedelta
from discord.ext import commands


class Track(wavelink.Track):
    __slots__ = ('requester',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.requester = kwargs.get('requester')


class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = asyncio.Queue()

    async def next(self) -> None:
        if self.is_playing:
            return

        #try:
         #   with async_timeout.timeout(300):
          #      await self.queue.get()
        #except asyncio.TimeoutError:
         #   return await self.destroy()

        await self.play(await self.queue.get())


class Music(commands.Cog, wavelink.WavelinkMixin):
    def __init__(self, bot):
        self.bot = bot
        self.bot.wavelink = wavelink.Client(bot=self.bot)
        self.bot.loop.create_task(self.start_lavalink())
        self.bot.loop.create_task(self.startup())

    async def start_lavalink(self):
        with open("./lavalink/lavalink.log", "w", encoding="utf-8") as f:
            print("[Music] Launching Lavalink...")
            subprocess.Popen(["java", "-jar", "./lavalink/Lavalink.jar", "-Djdk.tls.client.protocols=TLSv1.2"],
                             stdout=f, stderr=f)
            time.sleep(4)

    async def startup(self):
        await self.bot.wait_until_ready()
        await self.bot.wavelink.initiate_node(host="127.0.0.1", port=2333, rest_uri="http://127.0.0.1:2333",
                                              password="youshallnotpass", identifier="Main", region="us_central")

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node: wavelink.Node):
        print(f'[Music] Node ({node.identifier}) has successfuly started.')

    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_end")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node, payload):
        if payload.player.queue.qsize() == 0:
            return await payload.player.destroy()

        await payload.player.next()

    @commands.command(aliases=["join"], usage="join")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def connect(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        try:
            ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(title="Not Connected", description=f"You are not in a voice channel.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if player.is_connected:
            embed = discord.Embed(title="Already Connected", description=f"The player is already connected.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        await player.connect(ctx.author.voice.channel.id)
        embed = discord.Embed(title="Connected to channel",
                              description=f"Connected to **{ctx.author.voice.channel.name}**",
                              color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["p"], usage="play <name/url>")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def play(self, ctx, *, url):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        try:
            ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(title="Not Connected", description=f"You are not in a voice channel.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if not player.is_connected:
            await player.connect(ctx.author.voice.channel.id)

        if ctx.author.voice.channel.id != player.channel_id:
            embed = discord.Embed(title="Different Channel",
                                  description="You need to be in the same channel as the player.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if url.lower() == "sussy balls".lower():
            url = "https://www.youtube.com/watch?v=7zoLEOm8vEI"

        tracks = await self.bot.wavelink.get_tracks(f"ytsearch:{url}")

        track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
        await player.queue.put(track)

        # seconds = (track.length / 1000) % 60
        # seconds = int(seconds)
        # minutes = (track.length / (1000 * 60)) % 60
        # minutes = int(minutes)
        # hours = (track.length / (1000 * 60 * 60)) % 24
        # if track.length > 3600000:
        #    duration = f"{hours:.0f}h-{minutes:.0f}m-{seconds:.0f}s"
        # elif track.length > 60000:
        #    duration = f"{minutes:.0f}m-{seconds:.0f}s"
        # else:
        #    duration = f"{seconds:.0f} seconds"

        channel = self.bot.get_channel(player.channel_id)
        embed = discord.Embed(title=f"🎵 Added to queue | {channel}", color=discord.Color.green(),
                              timestamp=datetime.utcnow())
        embed.add_field(name="Track:", value=f"[{track.title}]({track.uri})")
        embed.add_field(name="Author:", value=f"{track.author}")
        embed.add_field(name="Duration:", value=str(timedelta(milliseconds=int(track.length))))
        embed.add_field(name="Requested By:", value=track.requester)
        embed.set_thumbnail(url=track.thumb)
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

        if not player.is_playing:
            await player.next()

    @commands.command(aliases=["vol"], usage="volume <number>")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def volume(self, ctx, number: int):
        try:
            ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(title="Not Connected", description=f"You are not in a voice channel.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            embed = discord.Embed(title="Not Connected", description=f"The player is not connected.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if not player.is_playing:
            embed = discord.Embed(title="Not Playing", description=f"The player is not playing.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if ctx.author.voice.channel.id != player.channel_id:
            embed = discord.Embed(title="Different Channel",
                                  description="You need to be in the same channel as the player.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        await player.set_volume(number)

        embed = discord.Embed(title="Volume Set", description=f"The volume has been set to `{player.volume}`",
                              color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["s"], usage="skip")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def skip(self, ctx):
        try:
            ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(title="Not Connected", description=f"You are not in a voice channel.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        if not player.is_connected:
            embed = discord.Embed(title="Not Connected", description=f"The player is not connected.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if not player.is_playing:
            embed = discord.Embed(title="Not Playing", description=f"The player is not playing.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if ctx.author.voice.channel.id != player.channel_id:
            embed = discord.Embed(title="Different Channel",
                                  description="You need to be in the same channel as the player.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        await player.stop()
        embed = discord.Embed(title="Skipped Song", description="The player has skipped the song.",
                              color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["np"], usage="nowplaying")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def nowplaying(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_connected:
            embed = discord.Embed(title="Not Connected", description=f"The player is not connected.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if not player.is_playing:
            embed = discord.Embed(title="Not Playing", description=f"The player is not playing.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        channel = self.bot.get_channel(player.channel_id)
        embed = discord.Embed(title=f"🎵 Now Playing | {channel}", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.add_field(name="Track:", value=f"[{player.current.title}]({player.current.uri})")
        embed.add_field(name="Author:", value=f"{player.current.author}")
        embed.add_field(name="Duration:", value=str(timedelta(milliseconds=int(player.current.length))))
        embed.add_field(name="Requested By:", value=player.current.requester)
        embed.set_thumbnail(url=player.current.thumb)
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)

        await ctx.send(embed=embed)

    @commands.command(aliases=["q"], usage="queue")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def queue(self, ctx):
        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)

        if not player.is_playing:
            embed = discord.Embed(title="Not Playing", description="The player is not playing.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if not player.is_connected:
            embed = discord.Embed(title="Not Connected", description="The player is not connected.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if player.queue.qsize() == 0:
            embed = discord.Embed(title="Queue Empty", description="The queue is empty.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        name = [track.title for track in player.queue._queue]
        name = '\n'.join(name)
        #uri = [track.uri for track in player.queue._queue]
        #uri = '\n'.join(uri)
        embed = discord.Embed(title="Songs In Queue", description=f"**Playing**: [{player.current.title}]({player.current.uri})\n\n{name}", color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)

        await ctx.send(embed=embed)

    @commands.command(aliases=["dc", "fuckoff"], usage="disconnect")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def disconnect(self, ctx):
        try:
            ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(title="Not Connected", description=f"You are not in a voice channel.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        if not player.is_connected:
            embed = discord.Embed(title="Not Connected", description=f"The player is not connected.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if ctx.author.voice.channel.id != player.channel_id:
            embed = discord.Embed(title="Different Channel",
                                  description="You need to be in the same channel as the player.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        await player.destroy()
        embed = discord.Embed(title="Disconnected", description="The player has disconnected.",
                              color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["stop"], usage="pause")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def pause(self, ctx):
        try:
            ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(title="Not Connected", description=f"You are not in a voice channel.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        if not player.is_connected:
            embed = discord.Embed(title="Not Connected", description=f"The player is not connected.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if not player.is_playing:
            embed = discord.Embed(title="Not Playing", description=f"The player is not playing.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if ctx.author.voice.channel.id != player.channel_id:
            embed = discord.Embed(title="Different Channel",
                                  description="You need to be in the same channel as the player.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if player.is_paused:
            embed = discord.Embed(title="Player Is Paused", description=f"The player has already been paused.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        await player.set_pause(True)
        embed = discord.Embed(title="Player Paused", description="The player has been paused.",
                              color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["start", "res"], usage="resume")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def resume(self, ctx):
        try:
            ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(title="Not Connected", description=f"You are not in a voice channel.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        if not player.is_connected:
            embed = discord.Embed(title="Not Connected", description=f"The player is not connected.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if not player.is_playing:
            embed = discord.Embed(title="Not Playing", description=f"The player is not playing.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if ctx.author.voice.channel.id != player.channel_id:
            embed = discord.Embed(title="Different Channel",
                                  description="You need to be in the same channel as the player.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if not player.is_paused:
            embed = discord.Embed(title="Player Not Paused", description=f"The player is not paused.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        await player.set_pause(False)
        embed = discord.Embed(title="Player Resumed", description="The player has been resumed.",
                              color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["pi"], usage="piano")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def piano(self, ctx):
        try:
            ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(title="Not Connected", description=f"You are not in a voice channel.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        if not player.is_connected:
            embed = discord.Embed(title="Not Connected", description=f"The player is not connected.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if not player.is_playing:
            embed = discord.Embed(title="Not Playing", description=f"The player is not playing.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if ctx.author.voice.channel.id != player.channel_id:
            embed = discord.Embed(title="Different Channel",
                                  description="You need to be in the same channel as the player.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        await player.set_eq(wavelink.Equalizer.piano())
        embed = discord.Embed(title="Equalizer Changed", description="The Equalizer has been changed to piano.",
                              color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["pi"], usage="piano")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def piano(self, ctx):
        try:
            ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(title="Not Connected", description=f"You are not in a voice channel.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        if not player.is_connected:
            embed = discord.Embed(title="Not Connected", description=f"The player is not connected.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if not player.is_playing:
            embed = discord.Embed(title="Not Playing", description=f"The player is not playing.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if ctx.author.voice.channel.id != player.channel_id:
            embed = discord.Embed(title="Different Channel",
                                  description="You need to be in the same channel as the player.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        await player.set_eq(wavelink.Equalizer.piano())
        embed = discord.Embed(title="Equalizer Changed", description="The Equalizer has been changed to piano.",
                              color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["fl"], usage="flat")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def flat(self, ctx):
        try:
            ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(title="Not Connected", description=f"You are not in a voice channel.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        if not player.is_connected:
            embed = discord.Embed(title="Not Connected", description=f"The player is not connected.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if not player.is_playing:
            embed = discord.Embed(title="Not Playing", description=f"The player is not playing.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if ctx.author.voice.channel.id != player.channel_id:
            embed = discord.Embed(title="Different Channel",
                                  description="You need to be in the same channel as the player.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        await player.set_eq(wavelink.Equalizer.flat())
        embed = discord.Embed(title="Equalizer Changed", description="The Equalizer has been changed to flat.",
                              color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["ml"], usage="metal")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def metal(self, ctx):
        try:
            ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(title="Not Connected", description=f"You are not in a voice channel.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        if not player.is_connected:
            embed = discord.Embed(title="Not Connected", description=f"The player is not connected.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if not player.is_playing:
            embed = discord.Embed(title="Not Playing", description=f"The player is not playing.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if ctx.author.voice.channel.id != player.channel_id:
            embed = discord.Embed(title="Different Channel",
                                  description="You need to be in the same channel as the player.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        await player.set_eq(wavelink.Equalizer.metal())
        embed = discord.Embed(title="Equalizer Changed", description="The Equalizer has been changed to metal.",
                              color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(usage="boost")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def boost(self, ctx):
        try:
            ctx.author.voice.channel
        except AttributeError:
            embed = discord.Embed(title="Not Connected", description=f"You are not in a voice channel.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player)
        if not player.is_connected:
            embed = discord.Embed(title="Not Connected", description=f"The player is not connected.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if not player.is_playing:
            embed = discord.Embed(title="Not Playing", description=f"The player is not playing.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        if ctx.author.voice.channel.id != player.channel_id:
            embed = discord.Embed(title="Different Channel",
                                  description="You need to be in the same channel as the player.",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
            return await ctx.send(embed=embed)

        await player.set_eq(wavelink.Equalizer.boost())
        embed = discord.Embed(title="Equalizer Changed", description="The Equalizer has been boosted.",
                              color=discord.Color.green(), timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Music(bot))
