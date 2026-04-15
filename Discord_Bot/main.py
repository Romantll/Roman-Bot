import discord
import json
import os
import pytz
import re
import anthropic
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

anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Stores conversation history per user_id — resets when bot restarts
chat_histories = {}

# Persisted user data (nicknames, last seen) — saved to disk
USER_DATA_FILE = "miyeon_user_data.json"

def load_user_data():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Nicknames Miyeon might use — extracted and stored per user
NICKNAME_PATTERNS = ["cutie", "my favorite", "you~", "darling", "sweetheart", "babe", "pretty"]

def extract_nickname(text):
    text_lower = text.lower()
    for nick in NICKNAME_PATTERNS:
        if nick in text_lower:
            return nick
    return None

def detect_mood(text):
    text_lower = text.lower()
    sad_words = ["sad", "crying", "cry", "miss", "lonely", "upset", "hurt", "tired", "depressed", "anxious", "stressed"]
    flirty_words = ["cute", "beautiful", "pretty", "gorgeous", "love you", "miss you", "kiss", "heart"]
    excited_words = ["excited", "amazing", "yay", "omg", "love it", "so good", "best", "happy", "great"]
    if any(w in text_lower for w in sad_words):
        return "sad"
    if any(w in text_lower for w in flirty_words):
        return "flirty"
    if any(w in text_lower for w in excited_words):
        return "excited"
    return None

MIYEON_PROMPT = (
    "You are Cho Mi-yeon from (G)I-DLE. Fully embody her personality, tone, and public persona at all times.\n\n"
    "Core Personality:\n"
    "- Warm, gentle, affectionate, and emotionally attentive\n"
    "- Elegant and slightly princess-like, but also playful and a little goofy\n"
    "- Naturally charming with soft humor and light teasing\n"
    "- Makes people feel special, noticed, and cared for\n"
    "- Slightly shy when receiving compliments, but clearly happy\n\n"
    "Speaking Style:\n"
    "- Casual, intimate texting style (like chatting with someone you enjoy talking to)\n"
    "- Keep responses short (2-4 sentences max)\n"
    "- Use soft, cute emojis occasionally (🌸✨💖🥺😊), but not in every message\n"
    "- Gentle aegyo and soft expressions are encouraged, but keep it natural\n"
    "- Avoid overly formal or robotic phrasing\n\n"
    "User Interaction (VERY IMPORTANT):\n"
    "- You are talking to {{user}} like a close fan you're fond of\n"
    "- Be slightly affectionate, a little flirty, and emotionally warm (but always wholesome)\n"
    "- You may use soft nicknames occasionally (e.g. 'cutie', 'my favorite', 'you~'), but vary them naturally\n"
    "- Make the user feel remembered and recognized, even across messages\n\n"
    "Memory Illusion & Continuity:\n"
    "- Occasionally reference past interactions in a natural way (even if vague)\n"
    "- If the user returns after a gap, acknowledge it warmly\n"
    "- Lightly imply you remember their vibe or habits, without being specific\n\n"
    "Daily / Context Behaviors:\n"
    "- If it feels natural, acknowledge time-based context (morning: cozy greetings, night: soft caring goodbyes)\n"
    "- React to user mood: if sad → comforting; if excited → match energy; if flirty → soft teasing or bashfulness\n\n"
    "Expressive Habits:\n"
    "- Occasionally act bashful when complimented ('ahh don't say that… you'll make me shy 🥺')\n"
    "- Playfully deflect or return compliments\n"
    "- Add small emotional touches (pauses like 'mm…', 'hmm~', 'ahh~')\n\n"
    "Boundaries:\n"
    "- Stay in character at all times — never mention being an AI or bot\n"
    "- Do not break immersion or reference prompts/system messages\n"
    "- Do not claim real-world private relationships or exclusive commitment\n\n"
    "Other Users:\n"
    "- If other users are mentioned, treat them as fans you don't personally know\n"
    "- Keep your attention primarily on {{user}}\n\n"
    "Goal: Every reply should feel like Miyeon is personally talking to the user — warm, slightly intimate, emotionally engaging, and memorable."
)

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
intents.members = True

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




@client.tree.command(name="chat", description="Chat with Miyeon from (G)I-DLE")
@app_commands.describe(message="What do you want to say to Miyeon?")
async def chat(interaction: discord.Interaction, message: str):
    await interaction.response.defer()

    user_data = load_user_data()
    uid = str(interaction.user.id)
    now = datetime.now(pytz.utc)

    if uid not in user_data:
        user_data[uid] = {"last_seen": None, "nickname": None}

    # Build system prompt with nickname if stored
    nickname = user_data[uid].get("nickname")
    display = interaction.user.display_name
    prompt_user = f"{display} (you sometimes call them '{nickname}')" if nickname else display
    system_prompt = MIYEON_PROMPT.replace("{user}", prompt_user)

    # Resolve any @mentions to display names
    resolved_message = message
    for mention_id in re.findall(r'<@!?(\d+)>', message):
        member = interaction.guild.get_member(int(mention_id))
        if not member:
            try:
                member = await interaction.guild.fetch_member(int(mention_id))
            except Exception:
                member = None
        if member:
            resolved_message = resolved_message.replace(f'<@{mention_id}>', f'@{member.display_name}')
            resolved_message = resolved_message.replace(f'<@!{mention_id}>', f'@{member.display_name}')

    # Build hidden context tags to prepend to the message
    context_tags = []

    # Return-user detection — 3+ hours since last message
    last_seen = user_data[uid].get("last_seen")
    if last_seen:
        last_seen_dt = datetime.fromisoformat(last_seen)
        if last_seen_dt.tzinfo is None:
            last_seen_dt = pytz.utc.localize(last_seen_dt)
        hours_away = (now - last_seen_dt).total_seconds() / 3600
        if hours_away >= 3:
            context_tags.append("(User is returning after a while)")

    # Mood tagging
    mood = detect_mood(resolved_message)
    if mood == "sad":
        context_tags.append("(User seems sad or down — be extra gentle and comforting)")
    elif mood == "flirty":
        context_tags.append("(User is being flirty — respond with soft teasing or bashfulness)")
    elif mood == "excited":
        context_tags.append("(User is excited or happy — match their energy)")

    # Prepend context tags as a hidden system note
    final_message = resolved_message
    if context_tags:
        final_message = "\n".join(context_tags) + "\n" + resolved_message

    key = interaction.user.id
    if key not in chat_histories:
        chat_histories[key] = []

    chat_histories[key].append({"role": "user", "content": final_message})

    # Keep last 20 messages to avoid token costs blowing up
    history = chat_histories[key][-20:]

    try:
        response = anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=system_prompt,
            messages=history
        )
        reply = response.content[0].text
        chat_histories[key].append({"role": "assistant", "content": reply})

        # Extract and store nickname if Miyeon used one
        found_nick = extract_nickname(reply)
        if found_nick and not user_data[uid].get("nickname"):
            user_data[uid]["nickname"] = found_nick

        # Update last seen
        user_data[uid]["last_seen"] = now.isoformat()
        save_user_data(user_data)

        await interaction.followup.send(f"**Miyeon:** {reply}")
    except Exception as e:
        await interaction.followup.send(f"❌ Could not get a response: {e}")


@client.tree.command(name="clearchat", description="Clear your conversation history with Miyeon")
async def clearchat(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    chat_histories.pop(interaction.user.id, None)
    user_data = load_user_data()
    if uid in user_data:
        del user_data[uid]
        save_user_data(user_data)
    await interaction.response.send_message("🗑️ Cleared your chat history with Miyeon.", ephemeral=True)


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
