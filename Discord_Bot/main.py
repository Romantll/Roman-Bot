import discord
import json
import os
import pytz
import re
from dateutil import parser
from datetime import datetime, timedelta
from discord.ext import tasks
from reminder_manager import add_reminder
from comebackSheet import get_upcoming_comebacks
from discord import app_commands
from redditpicture import get_random_image
from dotenv import load_dotenv
from idolImages import get_idol_image,get_available_idols
load_dotenv()

Allowed_User_IDS = [130824833528233984, 121081639571816449]  #User IDs of allowed users
REMINDER_FILE = "comeback_reminders.json"

class Client(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        check_reminders.start()
        print(f'Logged in as {self.user}!')
    
    async def on_message(self, message):
       if message.author == self.user:
           return
       
       if message.content.startswith('hello'):
           await message.channel.send(f'Hello {message.author}')

# Load reminders from JSON file
def load_reminders():
    if not os.path.exists(REMINDER_FILE):
        return []
    with open(REMINDER_FILE, 'r') as f:
        return json.load(f)

# Save reminders to JSON file
def save_reminders(reminders):
    with open(REMINDER_FILE, 'w') as f:
        json.dump(reminders, f, indent=4)



intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)

@client.tree.command(name="hello", description = "Says hello!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.mention}!")

#Code for the "/randompic" function
@client.tree.command(name="randompic", description="Sends a random image from a subreddit")
@app_commands.describe(subreddit="The name of subreddit")
async def randompic(interaction: discord.Interaction, subreddit: str):
    await interaction.response.defer()

    subreddit = subreddit.strip().lower().replace("r/","")
    post = await get_random_image(subreddit)
    if post:
        await interaction.followup.send(f"**{post.title}**\n{post.url}")
    else:
        await interaction.followup.send("No image posts found or subreddit does not exist")


@client.tree.command(name="addidolpic", description="Add a new image URL for a specific idol")
@app_commands.describe(name="Name of the idol", url="Direct image URL (e.g. from Imgur)")
async def addidolpic(interaction: discord.Interaction, name: str, url: str):
    await interaction.response.defer()

    #Check if the user is allowed
    if interaction.user.id not in Allowed_User_IDS:
        await interaction.followup.send("🚫 You don't have permission to use this command.")
        return

    #Auto-convert imgur page URLs to direct image links
    imgur_match = re.match(r'https?://imgur\.com/([a-zA-Z0-9]+)$', url)
    if imgur_match:
        image_id = imgur_match.group(1)
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.head(f'https://i.imgur.com/{image_id}', allow_redirects=True) as resp:
                    final_url = str(resp.url)
                    # Extract extension from the final redirected URL
                    for ext in ('.mp4', '.gif', '.png', '.jpeg', '.jpg'):
                        if final_url.lower().endswith(ext):
                            url = final_url
                            break
                    else:
                        url = f'https://i.imgur.com/{image_id}.jpg'
        except Exception:
            url = f'https://i.imgur.com/{image_id}.jpg'

    #Continue with image validation and JSON update...
    if not url.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".mp4")):
        await interaction.followup.send("❌ URL must end in .jpg, .jpeg, .gif, .png, or .mp4")
        return

    try:
        with open("idol_images.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    key = name.lower().strip()

    if key not in data:
        data[key] = []

    if url in data[key]:
        await interaction.followup.send(f"⚠️ That URL is already in the list for **{name.title()}**.")
        return

    data[key].append(url)

    with open("idol_images.json", "w") as f:
        json.dump(data, f, indent=2)

    await interaction.followup.send(f"✅ Added image to **{name.title()}**!")



#Code for the autocomplete inside the "/idolpic" function 
async def get_idol_autocomplete(interaction: discord.Interaction, current: str):
    idols = get_available_idols()
    return[
        app_commands.Choice(name=idol, value=idol)
        for idol in idols
        if current.lower() in idol.lower()
    ] [:25] #maximum discord allowewd choices

#Code for the "/idolpic" command
@client.tree.command(name="idolpic", description="Sends a random image of an idol")
@app_commands.describe(name="Name of the idol (e.g., Jo Yuri, Miyeon, Eunchae)")
@app_commands.autocomplete(name=get_idol_autocomplete)
async def idolpic(interaction: discord.Interaction, name: str):
    await interaction.response.defer()

    image_url = await get_idol_image(name)  # get the image first

    if image_url:
        if image_url.lower().endswith(".mp4"):
            await interaction.followup.send(f"**{name.title()}**\n{image_url}")
        else:
            embed = discord.Embed(title=f"{name.title()}", description="Here's your idol!")
            embed.set_image(url=image_url)
            await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(f"I couldn't find images for **{name.title()}**.")

#code for the "/ping" command mainly used for testing
@client.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong!")


@client.tree.command(name="comebacks", description="Shows upcoming comebacks")
async def comebacks(interaction: discord.Interaction):
    await interaction.response.defer()
    
    try:
        results = get_upcoming_comebacks()
    except Exception as e:
        await interaction.followup.send(f"❌ Could not fetch comeback data: {e}")
        return

    if not results:
        await interaction.followup.send("📭 No upcoming comebacks found.")
        return

    msg = "**📢 Upcoming Comebacks:**\n" + "\n".join(results[:10])
    await interaction.followup.send(msg)


@client.tree.command(name="addreminder", description="Set a reminder for a comeback")
@app_commands.describe(group="Group name (e.g., Jo Yuri, Miyeon, Red Velvet)")
async def addreminder(interaction: discord.Interaction, group: str):
    comebacks = get_upcoming_comebacks()

    # Try fuzzy match
    found = [c for c in comebacks if group.lower() in c.lower()]
    if not found:
        await interaction.response.send_message(f"❌ No comebacks found for **{group}**.")
        return

    # Get matched comeback string
    matched = found[0]
    await interaction.response.send_message(f"✅ Reminder set for **{group}** - {matched}!", ephemeral=True)

    try:
        # Split only at the LAST dash to get the date+time segment
        head, date_str = matched.rsplit("–", 1)
        date_str = date_str.strip()

        # Parse the date and time
        if "at" not in date_str:
            raise ValueError("Missing 'at' in date string")

        date_part, time_part = date_str.split("at")
        date_part = date_part.strip()
        time_part = time_part.replace("KST", "").strip()
        datetime_str = f"{date_part} {time_part}"

        # Parse KST and convert to UTC
        kst = pytz.timezone('Asia/Seoul')
        kst_naive = parser.parse(datetime_str)
        kst_time = kst.localize(kst_naive)
        utc_time = kst_time.astimezone(pytz.utc)

    except Exception as e:
        await interaction.followup.send(f"❌ Error parsing date/time: {e}", ephemeral=True)
        return

    # Create reminder times in UTC
    reminder_times = [
        (utc_time - timedelta(hours=1)).isoformat(),
        (utc_time - timedelta(minutes=30)).isoformat(),
        utc_time.isoformat(),
    ]

    # Save to reminders
    reminders = load_reminders()
    for t in reminder_times:
        reminders.append({
            "user_id": interaction.user.id,
            "channel_id": interaction.channel_id,
            "datetime_utc": t,
            "group": group,
        })
    save_reminders(reminders)

    await interaction.followup.send(
        f"🔔 You will be pinged **1h**, **30m**, and **at the time** of **{group}**’s comeback.\n\n"
        f"🗓️ {matched}", ephemeral=True
    )




@tasks.loop(minutes=1)
async def check_reminders():
    now_utc = datetime.now(pytz.utc)
    reminders = load_reminders()
    remaining = []

    for reminder in reminders:
        reminder_time = datetime.fromisoformat(reminder["datetime_utc"])
        if reminder_time.tzinfo is None:
            reminder_time = pytz.utc.localize(reminder_time)

        if now_utc >= reminder_time:
            channel = client.get_channel(reminder["channel_id"])
            if channel:
                await channel.send(f"🔔 <@{reminder['user_id']}> Reminder: **{reminder['group']}** has a comeback!")
        else:
            remaining.append(reminder)

    save_reminders(remaining)


client.run(os.getenv("DISCORD_TOKEN"))
