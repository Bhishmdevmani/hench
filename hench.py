import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os

# Bot setup - replace with your token
TOKEN = 'MTQ1ODg4MDAxMjAyMjMxNzE5OA.GtQtPd._iDC_TgyStF3NE4ffRHuFvFQhuBIgxfNaJcOxM'
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Suppress noise
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f'{bot.user} (Hench) has landed!')

@bot.command()
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send("Join a voice channel first!")
        return
    channel = ctx.author.voice.channel
    await channel.connect()

@bot.command()
async def play(ctx, *, url):
    if not ctx.voice_client:
        await ctx.invoke(bot.get_command('join'))
    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
    await ctx.send(f'Now playing: {player.title} [{player.duration}s]')

@bot.command()
async def pause(ctx):
    if ctx.voice_client.is_paused():
        return await ctx.send("Already paused!")
    ctx.voice_client.pause()
    await ctx.react(ctx.message, '⏸️')

@bot.command()
async def resume(ctx):
    if not ctx.voice_client.is_paused():
        return await ctx.send("Not paused!")
    ctx.voice_client.resume()
    await ctx.react(ctx.message, '▶️')

@bot.command()
async def stop(ctx):
    ctx.voice_client.stop()
    await ctx.react(ctx.message, '⏹️')

@bot.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()
    await ctx.react(ctx.message, '👋')

@bot.command()
async def volume(ctx, vol: int):
    if ctx.voice_client:
        ctx.voice_client.source.volume = vol / 100
        await ctx.send(f"Volume set to {vol}%")
    else:
        await ctx.send("Not in voice channel!")

bot.run(TOKEN)