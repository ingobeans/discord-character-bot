import discord, json, os, model, asyncio, gpt, requests
from discord.ext import commands
from dataclasses import dataclass
from translate import Translator

if not os.path.isfile("settings.json"):
    if input(f"There is no settings.json in {os.getcwd()}. Do you want to create it? (y/n): ").lower() != "y":
        quit()
    default_settings = '''{
    "bot_token":"enter bot token here",
    "pawankrd_key":"enter pawan.krd key here",
    "command_prefix":"!",
    "enter channel name here (you can have multiple channels as seperate keys, all with the following format)":
    {
        "global":false,
        "allowed_commands":["preset","list","get","debug","clear","username"],
        
        "DISABLED.webhook": "remove 'DISABLED.' to use a webhook url here. A webhook isn't required, but allows your presets to have custom avatars and usernames.",

        "presets":
            {
                "assistant":
                {
                    "content":"Conversation between an AI assistant and user.\\n\\n",
                    "username":"User",
                    "botname":"Assistant",

                    "DISABLED.avatar_url": "remove 'DISABLED.' to use an image URL for the avatar to use with this preset. Only available with a webhook. Enter avatar URL in this field"
                }
            }
    }
}'''
    with open("settings.json","w") as f:
        f.write(default_settings)
    

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
    use_gpt:bool
    translate:Translator
    translate_english:Translator
    avatar_url:str
    messages:str=""

@dataclass
class ChannelSettings:
    GLOBAL:bool
    PRESETS:dict
    ALLOWED_COMMANDS:list
    CHANNEL_NAME:str
    WEBHOOK:str

def remove_partial_suffix(text:str, suffix:str)->str:
    for i in range(1, len(suffix) + 1):
        partial_suffix = suffix[:i]
        if text.endswith(partial_suffix):
            return text[:-len(partial_suffix)]
    return text

def get_settings(channel_name:str)->ChannelSettings:
    settings_dict = GLOBAL_SETTINGS[channel_name]
    return ChannelSettings(settings_dict["global"],settings_dict["presets"],settings_dict["allowed_commands"],channel_name,settings_dict["webhook"] if "webhook" in settings_dict else None)

def get_name(name:str)->str:
    if name in name_overrides:
        return name_overrides[name]
    return name

def get_conversation(username:str,settings:ChannelSettings)->Conversation:
    if settings.GLOBAL:
        username="global"
    
    if not username in conversations[settings.CHANNEL_NAME]:
        c = settings.PRESETS[list(settings.PRESETS.keys())[0]]
        gpt = "use_gpt" in c and c["use_gpt"] == True
        translate = Translator(to_lang=c["translate"]) if "translate" in c else None
        translate_english = Translator(to_lang="en",from_lang=c["translate"]) if "translate" in c else None
        avatar_url = c["avatar_url"] if "avatar_url" in c else None
        conversations[settings.CHANNEL_NAME][username] = Conversation(c["content"],c["username"],c["botname"],gpt,translate,translate_english,avatar_url)
    
    return conversations[settings.CHANNEL_NAME][username]

async def generate_response(text:str,message,conversation:Conversation,settings:ChannelSettings):
    if conversation.use_gpt:
        resp = gpt.complete(text,stop=["\n\n"])
        print(f"used chat gpt to complete {text}")
    else:
        resp = model.complete(text,PAWAN_KRD_TOKEN,stop=[f"\n\n"],max_tokens=128)
    resp = remove_partial_suffix(resp,f"\n\n{conversation.username.format(name=get_name(message.author.display_name),username=message.author.name)}").strip() # respoonse wont stop exactly at the stop variable, as it generates in chunks. This function removes any leftovers

    conversation.messages+=f"{resp}\n\n"

    print(f"{message.author.name} -> {repr(resp)}")

    if conversation.translate != None:
        print(f"Translating response...")
        resp = conversation.translate.translate(resp)
    
    if settings.WEBHOOK != None:
        send_webhook_message(resp,settings,conversation)
        return
    
    await message.reply(resp,mention_author=False)

def send_webhook_message(message:str,settings:ChannelSettings,conversation:Conversation):
    botname = conversation.botname
    if not botname:
        if len(message.split(": ",1)) == 2:
            botname = message.split(": ",1)[0]
            message = message.split(": ",1)[1]
        else:
            botname = "System"
    data = {"content": message, "username": botname}
    if conversation.avatar_url != None:
        data = {
                    "avatar_url": conversation.avatar_url,
                    "content": message, 
                    "username": botname
                }
    requests.post(settings.WEBHOOK,data)
    
        

conversations = {}
name_overrides = {}

for channel in [k for k in list(GLOBAL_SETTINGS.keys()) if not k in ["bot_token","pawankrd_key","command_prefix"]]:
    conversations[channel] = {}


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the documents pile up."))
    print("Bot is online!")

@client.command(name="preset")
async def preset_command(ctx,presetname=None):
    global conversations
    settings = get_settings(ctx.channel.name)
    if not "preset" in settings.ALLOWED_COMMANDS:
        return
    if presetname == None:
        presetname = list(settings.PRESETS.keys())[0]
    if not presetname in settings.PRESETS:
        await ctx.reply(f"Preset {presetname} doesn't exist. Use {COMMAND_PREFIX}list to list available presets.",mention_author=False)
        return
    
    new_preset = settings.PRESETS[presetname]
    
    conversation = get_conversation(ctx.author.name,settings)
    conversation.start_text = new_preset["content"]
    conversation.username = new_preset["username"]
    conversation.botname = new_preset["botname"]
    conversation.messages = ""
    conversation.use_gpt = "use_gpt" in new_preset and new_preset["use_gpt"] == True
    conversation.translate = Translator(to_lang=new_preset["translate"]) if "translate" in new_preset else None
    conversation.translate_english = Translator(to_lang="en",from_lang=new_preset["translate"]) if "translate" in new_preset else None
    conversation.avatar_url = new_preset["avatar_url"] if "avatar_url" in new_preset else None

    await ctx.reply(f"Loaded preset {presetname}",mention_author=False)

@client.command(name="list")
async def list_command(ctx):
    settings = get_settings(ctx.channel.name)
    if not "list" in settings.ALLOWED_COMMANDS:
        return
    await ctx.reply("## Available presets:"+"".join(["\n\n* " + p for p in settings.PRESETS]),mention_author=False)

@client.command(name="clear")
async def clear_command(ctx):
    settings = get_settings(ctx.channel.name)
    if not "clear" in settings.ALLOWED_COMMANDS:
        return
    get_conversation(ctx.author.name,settings).messages = ""
    await ctx.reply("Cleared conversation!",mention_author=False)

@client.command(name="debug")
async def debug_command(ctx):
    settings = get_settings(ctx.channel.name)
    if not "debug" in settings.ALLOWED_COMMANDS:
        return
    await ctx.reply(f"```json\n{str(conversations)}```",mention_author=False)

@client.command(name="get")
async def get_command(ctx):
    settings = get_settings(ctx.channel.name)
    if not "get" in settings.ALLOWED_COMMANDS:
        return
    conversation = get_conversation(ctx.author.name,settings)
    await ctx.reply(f"{conversation.start_text}{conversation.messages}",mention_author=False)

@client.command(name="username")
async def username_command(ctx, *, username=None):
    global name_overrides
    settings = get_settings(ctx.channel.name)
    if not "username" in settings.ALLOWED_COMMANDS:
        return
    
    if username == None:
        username = ctx.author.display_name
    
    name_overrides[ctx.author.display_name] = username

    await ctx.reply(f"Set username to {username}",mention_author=False)

@client.event
async def on_message(message):
    global conversations
    if not message.channel.name in GLOBAL_SETTINGS or message.author.bot:
        return
    if message.content.startswith(COMMAND_PREFIX):
        await client.process_commands(message)
        return
    
    settings = get_settings(message.channel.name)

    author = message.author.name
    content = message.content
    
    conversation = get_conversation(author,settings)
    
    if conversation.translate_english != None:
        content = conversation.translate_english.translate(content)
        print(f"Translated: {content}")

    username = conversation.username.format(name=get_name(message.author.display_name),username=message.author.name)
    conversation.messages+=f"{username}: {content}\n\n{conversation.botname}: " if conversation.botname else f"{username}: {content}\n\n"
    
    asyncio.create_task(generate_response(conversation.start_text+conversation.messages,message,conversation,settings))

client.run(BOT_TOKEN)