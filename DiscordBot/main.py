import discord
from discord import app_commands
from redditpicture import get_random_image
from dotenv import load_dotenv
from idolImages import get_idol_image,get_available_idols 
import os
load_dotenv()

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


#Code for the autocomplete inside the "/idolpic" function 
async def get_idol_autocomplete(interaction: discord.Interaction, current: str):
    idols = get_available_idols()
    return[
        app_commands.Choice(name=idol, value=idol)
        for idol in idols
        if current.lower() in idol.lower()
    ] [:25] #maximum discord allowewd choices

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


@client.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong!")


client.run(os.getenv("DISCORD_TOKEN"))
