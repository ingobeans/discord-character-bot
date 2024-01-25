import discord, json, os, model
from discord.ext import commands
from dataclasses import dataclass

if not os.path.isfile("settings.json"):
    if input(f"There is no settings.json in {os.getcwd()}. Do you want to create it? (y/n): ").lower() != "y":
        quit()
    default_settings = {
        "bot_token":None,
        "pawankrd_key":None,
        "conversation_channel_name":None,
        "command_prefix":"!",
        "presets":
            {
                "default":{"content":"Conversation between an AI assistant and user.\n\n","username":"User","botname":"Assistant"}
            }
    }
    with open("settings.json","w") as f:
        json.dump(default_settings,f,indent=2)
    

with open("settings.json","r",encoding="utf-8") as f:
    SETTINGS = json.load(f)
    BOT_TOKEN = SETTINGS["bot_token"]
    PAWAN_KRD_TOKEN = SETTINGS["pawankrd_key"]
    CONVERSATION_CHANNEL_NAME = SETTINGS["conversation_channel_name"]
    PRESETS = SETTINGS["presets"]
    COMMAND_PREFIX = SETTINGS["command_prefix"]
    if BOT_TOKEN == None or PAWAN_KRD_TOKEN == None:
        print("Discord bot token or pawan.krd (https://discord.gg/pawan) key is missing from settings.json. Please add the missing settings.")
        quit()

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

@dataclass
class Conversation:
    start_text:str
    username:str
    botname:str
    messages:str=""

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
        await ctx.reply(f"Preset {presetname} doesn't exist. Use {COMMAND_PREFIX}list to list available presets.",mention_author=False)
        return
    
    new_preset = PRESETS[presetname]
    
    conversations[ctx.author.name] = Conversation(new_preset["content"],new_preset["username"],new_preset["botname"])
    
    await ctx.reply(f"Loaded preset {presetname}",mention_author=False)

@client.command()
async def list(ctx):
    await ctx.reply("## Available presets:"+"".join(["\n\n* " + p for p in PRESETS]),mention_author=False)

@client.command()
async def get(ctx):
    await ctx.send(conversations[ctx.author.name].messages)

@client.event
async def on_message(message):
    global conversations
    if (message.channel.name != CONVERSATION_CHANNEL_NAME and CONVERSATION_CHANNEL_NAME != None) or message.author.bot:
        return
    if message.content.startswith(COMMAND_PREFIX):
        await client.process_commands(message)
        return

    author = message.author.name

    if not author in conversations:
        conversations[author] = Conversation(PRESETS["default"]["content"],PRESETS["default"]["username"],PRESETS["default"]["botname"])

    conversations[author].messages+=f"{conversations[author].username}: {message.content}\n\n{conversations[author].botname}: "

    resp = model.complete(conversations[author].start_text+conversations[author].messages,PAWAN_KRD_TOKEN,stop=[f"\n\n{conversations[author].username}"],max_tokens=128)
    resp = remove_partial_suffix(resp,f"\n\n{conversations[author].username}").strip() # respoonse wont stop exactly at the stop variable, as it generates in chunks. This function removes any leftovers
    conversations[author].messages+=f"{resp}\n\n"

    print(f"{author} -> {repr(resp)}")

    await message.reply(resp,mention_author=False)

client.run(BOT_TOKEN)