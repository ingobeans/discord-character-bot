import discord, json, os, model
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
                "default":{"content":"Conversation between an AI assistant and user.\n\n","username":"User","botname":"Assistant"}
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

def remove_partial_suffix(text:str, suffix:str)->str:
    for i in range(1, len(suffix) + 1):
        partial_suffix = suffix[:i]
        if text.endswith(partial_suffix):
            return text[:-len(partial_suffix)]
    return text

conversations = {}

@client.event
async def on_ready():
    print("Bot is online!")

@client.command()
async def preset(ctx,presetname="default"):
    global conversations
    if not presetname in PRESETS:
        return
    
    new_preset = PRESETS[presetname]
    
    conversations[ctx.author.name] = Conversation(new_preset["content"],new_preset["username"],new_preset["botname"])
    
    await ctx.send(f"Loaded preset {presetname}, for {ctx.author.name}")

@client.command()
async def list(ctx):
    await ctx.reply("Available presets: \n\n"+"".join(["\n\n* " + p for p in PRESETS]),mention_author=False)

@client.command()
async def get(ctx):
    await ctx.send(conversations[ctx.author.name].messages)

@client.event
async def on_message(message):
    global conversations
    if message.channel.name != CONVERSATION_CHANNEL_NAME or message.author.bot:
        return
    if message.content.startswith("!"):
        await client.process_commands(message)
        return

    author = message.author.name

    if not author in conversations:
        conversations[author] = Conversation(PRESETS["default"]["content"],PRESETS["default"]["username"],PRESETS["default"]["botname"])

    conversations[author].messages+=f"{conversations[author].username}: {message.content}\n\n{conversations[author].botname}: "

    resp = model.complete(conversations[author].messages,PAWAN_KRD_TOKEN,stop=[f"\n\n{conversations[author].username}"],max_tokens=128)
    resp = remove_partial_suffix(resp,f"\n\n{conversations[author].username}") # respoonse wont stop exactly at the stop variable, as it generates in chunks. This function removes any leftovers
    conversations[author].messages+=f"{resp}\n"

    os.system("cls")
    print(repr(resp))

    await message.channel.send(resp)

client.run(BOT_TOKEN)