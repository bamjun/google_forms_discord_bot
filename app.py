import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
import requests
from discord.ext import commands


# Dummy server to pass health check
def run_dummy_server():
    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Health Check OK")

    server = HTTPServer(("0.0.0.0", 8000), HealthCheckHandler)
    server.serve_forever()


# Start dummy server in a separate thread
threading.Thread(target=run_dummy_server, daemon=True).start()


# URL of the deployed Google Apps Script web app
script_url = os.getenv("SCRIPT_URL")


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

    if "error" in response_json and response_json["error"] == "ID not found":
        await interaction.followup.send("No user found.", ephemeral=True)
        return

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


# AI API 키와 모델 설정
API_KEY = os.getenv("AIML_API_KEY")  # 실제 API 키로 대체
API_URL = "https://api.aimlapi.com/tts"  # g1_whisper-large 모델을 사용하는 TTS API URL
MODEL = "gpt-4o-mini"


# AIML API에 텍스트를 보내고 응답을 받는 함수
async def get_ai_response(content: str):
    # AIML API 호출
    response = requests.post(
        "https://api.aimlapi.com/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        json={
            "model": MODEL,  # AIML에서 사용할 모델
            "messages": [{"role": "user", "content": content}],
        },
    )
    # API 응답 파싱
    if response.status_code == 200:
        data = response.json()
        return data["choices"][0]["message"]["content"]  # AI 응답 메시지
    else:
        return "AI 응답을 가져오는 중 오류가 발생했습니다."


# Discord 명령어 처리
@bot.tree.command(name="ai", description="AI와 대화")
async def ai(interaction: discord.Interaction, content: str):
    try:
        # 사용자가 입력한 content를 AIML API에 보냄
        await interaction.response.defer()  # 응답 처리 시간을 주기 위한 defer 사용
        ai_response = await get_ai_response(content)

        # AI의 응답을 Discord 채널에 출력
        await interaction.followup.send(f"AI의 응답: {ai_response}")
    
    except discord.errors.NotFound:
        # 상호작용이 유효하지 않은 경우 처리
        print("Unknown interaction. The interaction might have expired.")
        await interaction.followup.send("AI 응답 중 오류가 발생했습니다. 다시 시도해 주세요.", ephemeral=True)
    
    except Exception as e:
        # 기타 에러 처리
        print(f"예기치 않은 오류 발생: {e}")
        await interaction.followup.send(f"AI 응답 중 오류가 발생했습니다: {e}", ephemeral=True)



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

        await message.channel.send(
            """
add bot : https://discord.com/oauth2/authorize?client_id=1279655946359935027
web page : https://bamjun.github.io/google_forms_discord_bot/
            """
        )

    # Call the command handler to process other commands
    await bot.process_commands(message)


@bot.event
async def on_guild_join(guild):
    # Send "Hello World" message to the first text channel the bot has permission to send messages in
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send(
                """
add bot : https://discord.com/oauth2/authorize?client_id=1279655946359935027
web page : https://bamjun.github.io/google_forms_discord_bot/

# Google Forms Discord Bot User Manual

## 1. Add Discord Bot
To begin, you need to add the bot to your Discord server. Use the bot invitation link to invite it to the server of your choice.

## 2. Find Google Form URL and Input Field ID
You will need to locate the URL of the Google Form and the ID of the input field where responses will be submitted. Follow these steps:

1. Access the Google Form you want to use.
2. Open the developer tools in your browser (usually by pressing the F12 key).
3. Navigate to the "Network" tab within the developer tools.
4. Submit a response to the form.
5. Look for the item labeled 'formResponse' in the network activity.
6. In the payload, find the number that follows 'entry.'. This number is the ID of the input field.

## 3. Set Up the Bot
To configure the bot, use the following command in the Discord chat:

`/setting [GoogleFormURL] [InputFieldID]`

### Example:
`/setting https://docs.google.com/forms/d/e/your-form-id/formResponse 1234567`

This will associate your Google Form and the specific input field with the bot.
## 4. Send Messages
Once the setup is complete, you can send messages to the Google Form using the bot with the following command:

`/add [message]`

### Example:
`/add Hello, this is a test message.`

This will submit the message to the specified input field in your Google Form.

"""
            )
            break


# Run the bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
