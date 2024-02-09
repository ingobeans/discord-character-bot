# Discord Character Bot

Discord bot to be customizable characters to chat with, powered by the free to use [Pawan.Krd](https://discord.gg/pawan) PAI-001 model.
You can create different presets for different characters, locked to channels in your server.
The bot can also be used together with a webhook in the channel, which allows the bot to take on different avatars and usernames for the different presets (Recommended).


# Commands
To use a command, in any channel thats configured in the settings.json, write the command prefix followed by a command, of the following:
* preset \<preset name\> - Load a preset
* list - Sends the available presets for that channel
* info - Sends preset info
* clear - Clears the current conversation
* username \<new name\> - Set the name you will appear as to the bot. Ex: username The God of Beans
* get - Returns the current conversation. (Can often fail due to message character count limits)
* debug - Returns all active conversations in JSON format. (Can often fail due to message character count limits)

The reload command can be used by any administrator in any channel. It reloads the settings.json, to update presets and settings.

# Customization
**Note**: you can probably just use the examples at the bottom of the page if you don't want to read all the following documentation.
### Global configuration
Settings.json customizes the bot presets, channel settings and api keys. If no settings.json is found the program will ask to generate one automatically.
The settings.json should include the keys: 
* "bot_token" - String, discord bot token
* "pawankrd_key" - String, Pawan.Krd key, can get free at [their discord](https://discord.gg/pawan)
* "command_prefix" - String, the prefix to use commands (can't be / )

### Channels
Next up, to add channels the bot will interact in, add the channel names as keys, with a value of the channel settings as an object. The object should include the keys:
* "global" - Boolean, whether all users should share a single conversation, or if all users should have their own conversation. **Important: before using, read the Presets paragraph (specifically under username)**
* "allowed_commands" - List of Strings, names of commands to be allowed
* (optional) "webhook" - String, webhook URL
* "presets" - Object containing presets. The keys of the object are preset names, the value is a preset object. If the key is "dm", it will be the settings for DMs (webhooks won't work in DMs).

### Presets
Presets are objects containing the keys:
* "content" - String, the initial text given to the bot, like the description. Should probably end with: \n\n
* "username" - String, the username that the user has in the eyes of the bot. If you write {user} in the field it will be replaced by the users display name (or custom name set with the !username command). Including {user} is almost a must have if the channel is set to global, since otherwise all users will appear as the same person to the LLM.
* "botname" - String, the name that the bot writes from.
* (optional) "avatar_url" - String, url to the custom avatar to use for the preset. **Only available if the channel has a webhook.**
* (optional) "temperature" - Float, temperature for the LLM to use, between 0 and 1. Higher means more random responses. Default is 0.7
* (optional) "use_gpt" - Boolean, whether to complete responses with GPT-3.5 rather than the PAI-001 model. Default is False. Do note that the gpt api has but a fraction of the context window that the PAI-001 model has.
* (optional) "fixed_botname" - Boolean, whether the bot is forced to use the botname or not. If false, it can choose to speak as any name, allowing support for multiple characters. Default true. Do still specify a "botname", as this is used in case the bot tries to speak as a user, then it will force the bot to speak as the botname instead.

Here is an example settings.json
```json
{
    "bot_token":"enter bot token here",
    "pawankrd_key":"enter pawan.krd key here",
    "command_prefix":"!",
    "bot-chat-channel-without-webhooks":
    {
        "global":false,
        "allowed_commands":["preset","list","get","debug","clear","username","info"],
        "presets":
            {
                "assistant":
                {
                    "content":"Conversation between an AI assistant and user.\n\n",
                    "username":"User",
                    "botname":"Assistant"
                }
            }
    },
    "bot-chat-channel-with-webhooks":
    {
        "global":false,
        "allowed_commands":["preset","list","get","debug","clear","username","info"],
        "webhook":"webhook url"
        "presets":
            {
                "assistant":
                {
                    "content":"Conversation between an AI assistant and user.\n\n",
                    "username":"User",
                    "botname":"Assistant",
                    "avatar_url":"https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/ChatGPT_logo.svg/800px-ChatGPT_logo.svg.png"
                }
            }
    },
    "dm": {
        "allowed_commands":["get","debug","clear","username","info"],
        "presets": {
            "assistant":
                {
                    "content":"Conversation between an AI assistant and user.\n\n",
                    "username":"{user}",
                    "botname":"Assistant",
                }
        }
    },
    "global-bot-channel":
    {
        "global":true,
        "allowed_commands":["preset","list","get","debug","clear","username","info"],
        "presets":
            {
                "assistant":
                {
                    "content":"Conversation between an AI assistant multiple users.\n\n",
                    "username":"{name}",
                    "botname":"Assistant"
                }
            }
    }
}
```
