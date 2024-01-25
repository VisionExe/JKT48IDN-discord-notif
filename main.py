import discord
from discord.ext import commands, tasks
import requests
import datetime
import time
import random

bot = commands.Bot(command_prefix='!')
CHANNEL_ID = 1157334655037616278

def get_livestream_data():
    api_url = 'https://mobile-api.idntimes.com/v3/livestreams'
    response = requests.get(api_url)
    data = response.json()
    jkt48_livestreams = [livestream for livestream in data.get('data', []) if 'JKT48' in livestream.get('creator', {}).get('username', '').lower() or 'jkt48' in livestream.get('creator', {}).get('username', '').lower()]
    return {'data': jkt48_livestreams}

last_messages = {}
live_stream_stats = {}

@tasks.loop(minutes=1)
async def check_finished_streams():
    print("Checking finished streams...")
    livestream_data = get_livestream_data()
    if 'data' in livestream_data and len(livestream_data['data']) > 0:
        print("Livestream data available. Checking for ended streams...")
        for livestream in livestream_data['data']:
            if livestream['status'].lower() == 'ended':
                print(f"Detected ended livestream: {livestream}")
                member_name = livestream.get('creator', {}).get('name', 'Unknown')
                channel_id = CHANNEL_ID
                channel = bot.get_channel(channel_id)
                start_time = livestream.get('started_at', 0)
                end_time = livestream.get('ended_at', 0)
                duration_seconds = end_time - start_time
                duration_minutes, duration_seconds = divmod(duration_seconds, 60)
                duration_hours, duration_minutes = divmod(duration_minutes, 60)
                summary_message = (
                    f"Live {member_name} telah berakhir.\n"
                    f"{member_name} mewarnai harimu selama "
                    f"{duration_hours:02}:{duration_minutes:02}:{duration_seconds:02}\n\n"
                    f"Start: {livestream.get('started_at_formatted', 'Unknown')}\n"
                    f"End: {livestream.get('ended_at_formatted', 'Unknown')}\n\n"
                    f"👥 {livestream.get('view_count', 0)}\n"
                    f"💬 {livestream.get('comment_count', 0)}"
                )
                await channel.send(summary_message)
                print(f"Notifikasi terkirim ke server atas nama {member_name}")
    else:
        print("No livestream data available. The member has finished streaming.")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="JKT48 Livestreams"))
    check_finished_streams.start()
    while True:
        await livestream_notification()
        time.sleep(15)

async def livestream_notification():
    livestream_data = get_livestream_data()
    if livestream_data and 'data' in livestream_data and len(livestream_data['data']) > 0:
        print("Livestream data available. Sending notifications...")
        for livestream in livestream_data['data']:
            await send_livestream_notification(livestream)
    for livestream in get_livestream_data()['data']:
        creator_name = livestream.get('creator', {}).get('name', 'Unknown')
        live_stream_stats[creator_name] = {'total_gold': 0}

async def send_livestream_notification(livestream):
    channel_id = CHANNEL_ID
    random_color = discord.Color(random.randint(0, 0xFFFFFF))
    title = livestream.get('title', 'No Title')
    playback_url = livestream.get('playback_url', '')
    thumbnail_url = livestream.get('image_url', '')
    view_count = livestream.get('view_count', 0)
    status = livestream.get('status', 'Unknown')
    creator = livestream.get('creator', {})
    creator_name = creator.get('name', 'Unknown')
    username = creator.get('username', 'Unknown')
    gift_icon_url = livestream.get('gift_icon_url', '')
    category_name = livestream.get('category', {}).get('name', 'Unknown')
    slug = livestream.get('slug', '')
    greeting = get_greeting(live_at)
    total_gold = live_stream_stats.get(creator_name, {}).get('total_gold', 0)
    embed = discord.Embed(
        title=title,
        description=f"{greeting}, si {creator_name} lagi live nih! Nonton yuk! 🎥\n"
                    f"**Pemirsa 👥:** {view_count}\n"
                    f"**Pembuat:** {creator_name}",
        color=random_color
    )
    embed.set_thumbnail(url=thumbnail_url)
    embed.add_field(name="Web Player", value=f"[Buka di Web Player]({playback_url})", inline=False)
    channel_url = f"https://www.idn.app/{username.lower().replace(' ', '')}/live/{slug}"
    embed.add_field(name="Channel", value=f"[Buka Channel]({channel_url})", inline=True)
    if gift_icon_url:
        embed.set_footer(text='Gift Icon')
        embed.set_footer(icon_url=gift_icon_url)
    embed.add_field(name="Kategori", value=category_name, inline=True)
    embed.add_field(name="Total Gold", value=total_gold, inline=True)
    channel = bot.get_channel(channel_id)
    if livestream['room_identifier'] in last_messages:
        last_message = await channel.fetch_message(last_messages[livestream['room_identifier']])
        await last_message.delete()
    sent_message = await channel.send(embed=embed)
    last_messages[livestream['room_identifier']] = sent_message.id
    print(f"Notifikasi terkirim, Member yang sedang stream: {creator_name}")

def get_greeting(live_at):
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
    live_time = datetime.datetime.utcfromtimestamp(int(live_at))
    live_time = live_time.replace(tzinfo=datetime.timezone.utc)
    live_time = live_time.astimezone(datetime.timezone(datetime.timedelta(hours=7)))
    if 6 <= now.hour < 12:
        return "Selamat pagi"
    elif 12 <= now.hour < 15:
        return "Selamat siang"
    elif 15 <= now.hour < 20:
        return "Selamat sore"
    elif 20 <= now.hour < 24:
        return "Selamat malam"
    else:
        return "Selamat malam"

if __name__ == '__main__':
    print("Bot is starting...")
    bot.run('MTIwMDExOTg4MDY3OTE4MjUyNg.GZg5tN.hJp1_t5foaIrUq_YREf7AVL4EXCRl5ttlqkTkA')