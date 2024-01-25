import discord, json, os, model, asyncio
from discord.ext import commands
from dataclasses import dataclass
from threading import Thread

if not os.path.isfile("settings.json"):
    if input(f"There is no settings.json in {os.getcwd()}. Do you want to create it? (y/n): ").lower() != "y":
        quit()
    default_settings = {
        "bot_token":None,
        "pawankrd_key":None,
        "conversation_channel_name":None,
        "command_prefix":"!",
        "global":False,
        "presets":
            {
                "assistant":{"content":"Conversation between an AI assistant and user.\n\n","username":"User","botname":"Assistant"}
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
    GLOBAL = SETTINGS["global"]
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

def get_conversation(username:str)->Conversation:
    if GLOBAL:
        username="global"
    
    if not username in conversations:
        c = PRESETS[list(PRESETS.keys())[0]]
        conversations[username] = Conversation(c["content"],c["username"],c["botname"])
    
    return conversations[username]

async def generate_response(text:str,message,conversation:Conversation):
    resp = model.complete(text,PAWAN_KRD_TOKEN,stop=[f"\n\n"],max_tokens=128)
    resp = remove_partial_suffix(resp,f"\n\n{conversation.username.format(username=message.author.name)}").strip() # respoonse wont stop exactly at the stop variable, as it generates in chunks. This function removes any leftovers
    conversation.messages+=f"{resp}\n\n"

    print(f"{message.author.name} -> {repr(resp)}")

    await message.reply(resp,mention_author=False)

conversations = {}

@client.event
async def on_ready():
    print("Bot is online!")

@client.command(name="preset")
async def preset_command(ctx,presetname=None):
    global conversations
    if presetname == None:
        presetname = list(PRESETS.keys())[0]
    if not presetname in PRESETS:
        await ctx.reply(f"Preset {presetname} doesn't exist. Use {COMMAND_PREFIX}list to list available presets.",mention_author=False)
        return
    
    new_preset = PRESETS[presetname]
    
    conversations[ctx.author.name] = Conversation(new_preset["content"],new_preset["username"].format(username=ctx.author.name),new_preset["botname"])
    
    await ctx.reply(f"Loaded preset {presetname}",mention_author=False)

@client.command(name="list")
async def list_command(ctx):
    await ctx.reply("## Available presets:"+"".join(["\n\n* " + p for p in PRESETS]),mention_author=False)

@client.command(name="clear")
async def clear_command(ctx):
    get_conversation(ctx.author.name).messages = ""
    await ctx.reply("Cleared conversation!",mention_author=False)

@client.command(name="get")
async def get_command(ctx):
    conversation = get_conversation(ctx.author.name)
    await ctx.send(f"{conversation.start_text}{conversation.messages}")

@client.event
async def on_message(message):
    global conversations
    if (message.channel.name != CONVERSATION_CHANNEL_NAME and CONVERSATION_CHANNEL_NAME != None) or message.author.bot:
        return
    if message.content.startswith(COMMAND_PREFIX):
        await client.process_commands(message)
        return

    author = message.author.name
    
    conversation = get_conversation(author)

    conversation.messages+=f"{conversation.username.format(username=author)}: {message.content}\n\n{conversation.botname}: "
    
    asyncio.create_task(generate_response(conversation.start_text+conversation.messages,message,conversation))

client.run(BOT_TOKEN)