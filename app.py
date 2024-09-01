import os

import discord
import requests
from discord.ext import commands
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Dummy server to pass health check
def run_dummy_server():
    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Health Check OK')

    server = HTTPServer(('0.0.0.0', 8000), HealthCheckHandler)
    server.serve_forever()

# Start dummy server in a separate thread
threading.Thread(target=run_dummy_server, daemon=True).start()




# URL of the deployed Google Apps Script web app
script_url = script_url = os.getenv("SCRIPT_URL")

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# Define the /add command (Google Forms example)
@bot.tree.command(name="add", description="Add content to Google Forms")
async def add(interaction: discord.Interaction, content: str):
    user_id = str(interaction.user.id)

    # Send a quick response
    await interaction.response.defer(thinking=True)

    # Send a GET request to the Google Apps Script API to get the content URL and entry number
    params = {
        "userId": user_id,
    }
    script_response = requests.get(script_url, params=params)
    response_json = script_response.json()

    url = response_json["content"]

    # Set the entry number corresponding to each field in the Google Forms
    form_data = {
        "entry." + str(response_json["entry"]): content,  # Content entered by the user
    }

    # Submit the form via a POST request
    response = requests.post(url, data=form_data)

    # Send a message based on the result of the request
    if response.status_code == 200:
        await interaction.followup.send(f"Content successfully submitted: {content}")
    else:
        await interaction.followup.send(f"Submission failed: {response.status_code}")


# Define the /setting command (Save Google Forms URL)
@bot.tree.command(name="setting", description="Save the URL of your Google Form")
async def setting(interaction: discord.Interaction, content: str, entry: str):
    user_id = str(interaction.user.id)

    # Send a POST request to the Google Apps Script API to save the URL
    data = {"userId": user_id, "content": content, "entry": entry}

    await interaction.response.defer(thinking=True)

    response = requests.post(script_url, data=data)

    if response.status_code == 200:
        await interaction.followup.send("Google Form URL successfully saved.")
    else:
        await interaction.followup.send(f"Failed to save URL: {response.status_code}")


@bot.event
async def on_ready():
    await bot.tree.sync()  # Sync slash commands to the server


@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Respond with "hello" if the user says "hi"
    if message.content.lower() == "hi":

        await message.channel.send("hello")

    # Call the command handler to process other commands
    await bot.process_commands(message)


@bot.event
async def on_guild_join(guild):
    # Send "Hello World" message to the first text channel the bot has permission to send messages in
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send("Hello World")
            break


# Run the bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
