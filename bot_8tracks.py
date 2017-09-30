from discord.ext import commands
from discord import VoiceClient, Game
from api_8tracks import SortTypes, query_8tracks_mixsets, query_8tracks_mixdetails
from channelobjects import Song, channel_state, mix_option
from restart import restart_program
import discord
import random
import api_8tracks
import transaction
import channelobjects
from BTrees.OOBTree import OOBTree

channel_states = OOBTree()
currentsortType = SortTypes.hot




if not discord.opus.is_loaded():
    discord.opus.load_opus('libopus-0.x64.dll')

youtube_dl_options = dict(
    format="bestaudio/best",
    extractaudio=True,
    audioformat="mp3",
    noplaylist=True,
    default_search="auto",
    quiet=False,
    nocheckcertificate=True
)
ffmpeg_before_options = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 10"









bot = commands.Bot(command_prefix='~', description='''test''')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    game = Game()
    game.name = '~help'
    await bot.change_status(game=game)

# @bot.command()
# async def commands():
#     help_message = 'commands are \n ~tags [list of tags]\n ~keyword [keyword]\n ~artist [artistname]\n ~all\n ~skip\n ~clear\n ~pause\n ~resume\n ~nowplaying\n ~queue\n'
#     await bot.say(help_message)


@bot.command()
async def sort(sorttype: str):
    """sets sort type choices are hot,recent and popular"""
    global currentsortType
    currentsortType = SortTypes[sorttype]
    await bot.say('Sort type set to ' + sorttype)


def get_current_channel(ctx):
    global channel_states
    channels: OOBTree = channel_states
    text_channel = ctx.message.channel
    current_channel_state = channel_state()
    print("checking for text channel : " + str(text_channel.id))
    if(channels.has_key(text_channel.id)):
        print("channel found : " + str(text_channel.id))
        current_channel_state = channels[text_channel.id]
    else:
        print("creating channel: " + str(text_channel.id))
        current_channel_state.id = text_channel.id
        channels.insert(current_channel_state.id,current_channel_state)
    return current_channel_state


@bot.command(pass_context=True)
async def tags(ctx, *tags: str):
    """Search for playlists by tags, accepts a list of tags"""
    current_channel_state = get_current_channel(ctx)
    current_channel_state.clear_options()
    query = query_8tracks_mixsets()
    result = await query.by_tags(tags).sort(currentsortType).top(10).get_results_cleaned()
    bot_message = ''
    for key, value in result.items():
        option = mix_option()
        option.mixid = key
        option.mixname = value
        i = current_channel_state.add_option(option)
        bot_message = bot_message + str(i + 1) + ".   " + value + '\n'
    await bot.say(bot_message)


@bot.command(pass_context=True)
async def artist(ctx, artist_name: str):
    """Search for playlists by artistname, accepts a single artist name"""
    current_channel_state = get_current_channel(ctx)
    current_channel_state.clear_options()
    query = query_8tracks_mixsets()
    result = await query.by_artist(artist_name).sort(currentsortType).top(10).get_results_cleaned()
    bot_message = ''
    for key, value in result.items():
        option = mix_option()
        option.mixid = key
        option.mixname = value
        i = current_channel_state.add_option(option)
        bot_message = bot_message + str(i + 1) + ".   " + value + '\n'
    await bot.say(bot_message)

@bot.command(pass_context=True)
async def keyword(ctx, keyword: str):
    """Search for playlists by keyword, accepts a single keyword"""
    current_channel_state = get_current_channel(ctx)
    current_channel_state.clear_options()
    query = query_8tracks_mixsets()
    result = await query.by_keyword(keyword).sort(currentsortType).top(10).get_results_cleaned()
    bot_message = ''
    for key, value in result.items():
        option = mix_option()
        option.mixid = key
        option.mixname = value
        i = current_channel_state.add_option(option)
        bot_message = bot_message + str(i + 1) + ".   " + value + '\n'
    await bot.say(bot_message)

@bot.command(pass_context=True)
async def all(ctx):
    """Get default list of playlists orderred by current sort type"""
    current_channel_state = get_current_channel(ctx)
    current_channel_state.clear_options()
    query = query_8tracks_mixsets()
    result = await query.all().sort(currentsortType).top(10).get_results_cleaned()
    bot_message = ''
    for key, value in result.items():
        option = mix_option()
        option.mixid = key
        option.mixname = value
        i = current_channel_state.add_option(option)
        bot_message = bot_message + str(i + 1) + ".   " + value + '\n'
    await bot.say(bot_message)


@bot.command(pass_context=True)
async def play(ctx, number: int):
    """plays chosen playlist, input is the number from a previous tags,artist,keyword or all command"""
    current_channel_state: channel_state = get_current_channel(ctx)
    author = ctx.message.author
    server = author.server
    voice_channel = author.voice_channel
    
    vc: VoiceClient
    if bot.is_voice_connected(server):
        vc = bot.voice_client_in(server)
    else:
        vc = await bot.join_voice_channel(voice_channel)
    
    query = query_8tracks_mixdetails()
    result = await query.of_id(current_channel_state.mix_options[number-1].mixid).get_results_cleaned()
    for key, value in result.items():
        player = await vc.create_ytdl_player("ytsearch:" + value, ytdl_options=youtube_dl_options,after=current_channel_state.play_next,
                                                      before_options=ffmpeg_before_options)
        song = Song( name=value, player=player)
        current_channel_state.add_queue(song)
        current_channel_state.play_now()
    await bot.say('Added ' + str(len(result)) + ' songs into queue.')


@bot.command(pass_context=True)
async def skip(ctx):
    """skips current song"""
    current_channel_state: channel_state = get_current_channel(ctx)
    current_channel_state.current_queue_item().player.stop()

@bot.command(pass_context=True)
async def clear(ctx):
    """clears queue"""
    current_channel_state: channel_state = get_current_channel(ctx)
    current_player = current_channel_state.current_queue_item().player
    current_channel_state.empty_queue()
    current_player.stop()


@bot.command(pass_context=True)
async def nowplaying(ctx):
    """title of song playing right now"""
    current_channel_state: channel_state = get_current_channel(ctx)
    await bot.say('Now playing : ' + current_channel_state.current_queue_item().player.title)

@bot.command(pass_context=True)
async def queue(ctx):
    """current queue"""
    current_channel_state: channel_state = get_current_channel(ctx)
    bot_message = 'Current queue is :\n'
    k = 1
    try:
        for i in range (current_channel_state.song_queue_pos, current_channel_state.song_queue.maxKey()):
            song = current_channel_state.song_queue[i]
            bot_message = bot_message + str(k) + '.   ' + song.player.title + '(' + seconds_to_hms(song.player.duration) + ')\n'
            k = k + 1
    except ValueError:
        bot_message = 'Queue is empty!'
    await bot.say(bot_message)

def seconds_to_hms(seconds: int):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return '{:0>2}:{:0>2}:{:0>2}'.format(h, m, s)


@bot.command(pass_context=True)
async def pause(ctx):
    """current queue"""
    current_channel_state: channel_state = get_current_channel(ctx)
    current_channel_state.pause()
    await bot.say('Paused.')    

@bot.command(pass_context=True)
async def resume(ctx):
    """current queue"""
    current_channel_state: channel_state = get_current_channel(ctx)
    current_channel_state.resume()
    await bot.say('Resumed.')    

@bot.command(pass_context=True)
async def rickroll(ctx):
    """queue rick roll"""
    current_channel_state: channel_state = get_current_channel(ctx)
    author = ctx.message.author
    server = author.server
    voice_channel = author.voice_channel
    
    vc: VoiceClient
    if bot.is_voice_connected(server):
        vc = bot.voice_client_in(server)
    else:
        vc = await bot.join_voice_channel(voice_channel)

    player = await vc.create_ytdl_player("ytsearch:rick roll")
    song = Song( name='rick roll', player=player)
    current_channel_state.add_queue(song)
    current_channel_state.play_now()
    await bot.say('Rick rolling has been scheduled!')

@bot.command()
async def roll(dice : str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await bot.say('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await bot.say(result)

@bot.command(description='For when you wanna settle the score some other way')
async def choose(*choices : str):
    """Chooses between multiple choices."""
    await bot.say(random.choice(choices))

@bot.command()
async def repeat(times : int, content='repeating...'):
    """Repeats a message multiple times."""
    for i in range(times):
        await bot.say(content)

@bot.command()
async def credits():
    """Who made me!"""
    await bot.say('sh0ck_wave made me!')

@bot.command()
async def restart():
    await bot.say('Restarting!')
    restart_program()

bot.run('MzYwNzc3MDA5NjQwNjM2NDE3.DKafUw.XCpw92ASMt8DZ43Do2lvgPTwSAo')
