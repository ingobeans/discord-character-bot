import discord, json, os, model, asyncio
from discord.ext import commands
from dataclasses import dataclass
from threading import Thread

if not os.path.isfile("settings.json"):
    if input(f"There is no settings.json in {os.getcwd()}. Do you want to create it? (y/n): ").lower() != "y":
        quit()
    default_settings = {
        "bot_token":"enter bot token here",
        "pawankrd_key":"enter pawan.krd key here",
        "command_prefix":"!",
        "enter channel name here (you can have multiple channels as seperate keys, all with the following format)":
        {
            "global":False,
            "presets":
                {
                    "assistant":
                    {
                        "content":"Conversation between an AI assistant and user.\n\n",
                        "username":"User",
                        "botname":"Assistant"
                    }
                }
        }
    }
    with open("settings.json","w") as f:
        json.dump(default_settings,f,indent=2)
    

with open("settings.json","r",encoding="utf-8") as f:
    GLOBAL_SETTINGS = json.load(f)
    BOT_TOKEN = GLOBAL_SETTINGS["bot_token"]
    PAWAN_KRD_TOKEN = GLOBAL_SETTINGS["pawankrd_key"]
    COMMAND_PREFIX = GLOBAL_SETTINGS["command_prefix"]
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

@dataclass
class ChannelSettings:
    GLOBAL:bool
    PRESETS:dict
    CHANNEL_NAME:str

def remove_partial_suffix(text:str, suffix:str)->str:
    for i in range(1, len(suffix) + 1):
        partial_suffix = suffix[:i]
        if text.endswith(partial_suffix):
            return text[:-len(partial_suffix)]
    return text

def get_settings(channel_name:str)->ChannelSettings:
    settings_dict = GLOBAL_SETTINGS[channel_name]
    return ChannelSettings(settings_dict["global"],settings_dict["presets"],channel_name)

def get_conversation(username:str,settings:ChannelSettings)->Conversation:
    if settings.GLOBAL:
        username="global"
    
    if not settings.CHANNEL_NAME in conversations:
        conversations[settings.CHANNEL_NAME] = {}
    
    if not username in conversations[settings.CHANNEL_NAME]:
        c = settings.PRESETS[list(settings.PRESETS.keys())[0]]
        conversations[settings.CHANNEL_NAME][username] = Conversation(c["content"],c["username"],c["botname"])
    
    return conversations[settings.CHANNEL_NAME][username]

async def generate_response(text:str,message,conversation:Conversation):
    resp = model.complete(text,PAWAN_KRD_TOKEN,stop=[f"\n\n"],max_tokens=128)
    resp = remove_partial_suffix(resp,f"\n\n{conversation.username.format(name=message.author.display_name,username=message.author.name)}").strip() # respoonse wont stop exactly at the stop variable, as it generates in chunks. This function removes any leftovers
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
    settings = get_settings(ctx.channel.name)
    if presetname == None:
        presetname = list(settings.PRESETS.keys())[0]
    if not presetname in settings.PRESETS:
        await ctx.reply(f"Preset {presetname} doesn't exist. Use {COMMAND_PREFIX}list to list available presets.",mention_author=False)
        return
    
    new_preset = settings.PRESETS[presetname]
    
    conversations[settings.CHANNEL_NAME][ctx.author.name] = Conversation(new_preset["content"],new_preset["username"].format(username=ctx.author.name),new_preset["botname"])
    
    await ctx.reply(f"Loaded preset {presetname}",mention_author=False)

@client.command(name="list")
async def list_command(ctx):
    settings = get_settings(ctx.channel.name)
    await ctx.reply("## Available presets:"+"".join(["\n\n* " + p for p in settings.PRESETS]),mention_author=False)

@client.command(name="clear")
async def clear_command(ctx):
    settings = get_settings(ctx.channel.name)
    get_conversation(ctx.author.name,settings).messages = ""
    await ctx.reply("Cleared conversation!",mention_author=False)

@client.command(name="debug")
async def debug_command(ctx):
    await ctx.reply(f"```json\n{str(conversations)}```",mention_author=False)

@client.command(name="get")
async def get_command(ctx):
    settings = get_settings(ctx.channel.name)
    conversation = get_conversation(ctx.author.name,settings)
    await ctx.send(f"{conversation.start_text}{conversation.messages}")

@client.event
async def on_message(message):
    global conversations
    settings = get_settings(message.channel.name)
    if not message.channel.name in GLOBAL_SETTINGS or message.author.bot:
        return
    if message.content.startswith(COMMAND_PREFIX):
        await client.process_commands(message)
        return

    author = message.author.name
    
    conversation = get_conversation(author,settings)

    username = conversation.username.format(name=message.author.display_name,username=message.author.name)
    conversation.messages+=f"{username}: {message.content}\n\n{conversation.botname}: " if conversation.botname else f"{username}: {message.content}\n\n"
    
    asyncio.create_task(generate_response(conversation.start_text+conversation.messages,message,conversation))

client.run(BOT_TOKEN)