import discord, random, json, os
from discord.ext import commands
from dataclasses import dataclass

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

if not os.path.isfile("settings.json"):
    if input(f"There is no settings.json in {os.getcwd()}. Do you want to create it? (y/n): ").lower() != "y":
        quit()
    default_settings = {
        "bot_token":None,
        "pawankrd_key":None,
        "conversation_channel_name":None,
        "presets":
            {
                "default":{"content":"Conversation between an AI assistant and user.","username":"User","botname":"Assistant"}
            }
    }
    with open("settings.json","w") as f:
        json.dump(default_settings,f,indent=2)
    

with open("settings.json","r") as f:
    SETTINGS = json.load(f)
    BOT_TOKEN = SETTINGS["bot_token"]
    PAWAN_KRD_TOKEN = SETTINGS["pawankrd_key"]
    CONVERSATION_CHANNEL_NAME = SETTINGS["conversation_channel_name"]
    PRESETS = SETTINGS["presets"]
    if BOT_TOKEN == None or PAWAN_KRD_TOKEN == None:
        print("Discord bot token or pawan.krd (https://discord.gg/pawan) key is missing from settings.json. Please add the missing settings.")
        quit()

@dataclass
class Conversation:
    messages:str
    username:str
    botname:str

conversations = {}

@client.event
async def on_ready():
    print("Bot is online!")

@client.command()
async def preset(ctx,presetname):
    global conversations
    if not presetname in PRESETS:
        return
    
    new_preset = PRESETS[presetname]
    
    conversations[ctx.author.name] = Conversation(new_preset["content"],new_preset["username"],new_preset["botname"])
    
    await ctx.send(f"Loaded preset {presetname}, for {ctx.author.name}")

@client.event
async def on_message(message):
    if message.channel.name != CONVERSATION_CHANNEL_NAME:
        return
    
    author = message.author.name
    conversation:Conversation = conversations[author]
    await message.channel.send(f"{message.author.name}, you are chatting as {conversation.username}")
    
    await client.process_commands(message)

client.run(BOT_TOKEN)