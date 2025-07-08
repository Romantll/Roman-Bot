import discord
import json
from comebackSheet import get_upcoming_comebacks
from discord import app_commands
from redditpicture import get_random_image
from dotenv import load_dotenv
from idolImages import get_idol_image,get_available_idols 
import os
load_dotenv()

Allowed_User_IDS = [130824833528233984, 121081639571816449]  #User IDs of allowed users


class Client(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        print(f'Logged in as {self.user}!')
    
    async def on_message(self, message):
       if message.author == self.user:
           return
       
       if message.content.startswith('hello'):
           await message.channel.send(f'Hello {message.author}')
    
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

    #Continue with image validation and JSON update...
    if not url.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
        await interaction.followup.send("❌ URL must end in .jpg, .jpeg, .gif, or .png")
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
        embed = discord.Embed(title=f"{name.title()}", description="Here's your idol!")
        embed.set_image(url=image_url)
        await interaction.followup.send(embed=embed)  #one clean response
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
        await interaction.followup.send("❌ Could not fetch comeback data.")
        return

    if not results:
        await interaction.followup.send("📭 No upcoming comebacks found.")
        return

    msg = "**📢 Upcoming Comebacks:**\n" + "\n".join(results[:10])
    await interaction.followup.send(msg)



client.run(os.getenv("DISCORD_TOKEN"))
