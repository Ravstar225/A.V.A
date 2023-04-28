import asyncio
import base64
import io
import time
from collections import deque

import aiohttp
import discord
import requests
import yaml
from fuzzywuzzy import process
from PIL import Image, PngImagePlugin

class ChatBot(discord.Client):
    def __init__(self, *args, **kwargs,):
        super().__init__(*args, **kwargs)
        self.channel_messages = {}
        self.channel_messages_determiner = {}
        self.channel_messages_nouns = {}
        self.thinking = False
        self.lock = asyncio.Lock()

    def is_trigger_word(self, word, trigger_words, threshold=95):
        best_match = process.extractOne(word, trigger_words)
        return best_match[1] >= threshold
    
    def add_message(self, channel_id, author, content):
        if channel_id not in self.channel_messages:
            self.channel_messages[channel_id] = deque(maxlen=10)
        formatted_message = f"###{author}: {content}"
        self.channel_messages[channel_id].append(formatted_message)

    def add_message_determiner(self, channel_id, author, content):
        if channel_id not in self.channel_messages_determiner:
            self.channel_messages_determiner[channel_id] = deque(maxlen=1)
        formatted_message = f"###{author}: {content}"
        self.channel_messages_determiner[channel_id].append(formatted_message)

    def add_message_noun(self, channel_id, author, content):
        if channel_id not in self.nouns:
            self.channel_messages_nouns[channel_id] = deque(maxlen=3)
        formatted_message = f"###{author}: {content}"
        self.channel_messages_nouns[channel_id].append(formatted_message)

    async def on_ready(self):
        print(f'{self.user} is connected to the following servers:')
        for guild in self.guilds:
            print(f'{guild.name} (id: {guild.id})')

    #generates an Image with stable diffusion and sends it in current channel
    async def generate_and_send_image(self, message, Nouns_first_line, config):
        url = config["bot"]["stable_url"]
        override_settings = {}
        payload = {
            "prompt": config["bot"]["diffusion_params"]["prompt_starter"] + Nouns_first_line,
            "steps": config["bot"]["diffusion_params"]["steps"],
            "negative_prompt": config["bot"]["diffusion_params"]["negative_prompt"],
            "sampler_name": config["bot"]["diffusion_params"]["sampler_name"],
            'cfg_scale': config["bot"]["diffusion_params"]["cfg_scale"],
            'width': config["bot"]["diffusion_params"]["width"],
            'height': config["bot"]["diffusion_params"]["height"],
            "override_settings": override_settings
            }
        async with message.channel.typing():
            response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=payload)
        r = response.json()
        for i in r['images']:
            image = Image.open(io.BytesIO(base64.b64decode(i.split(",", 1)[0])))
            png_payload = {
                "image": "data:image/png;base64," + i
            }
            response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)
            pnginfo = PngImagePlugin.PngInfo()
            pnginfo.add_text("parameters", response2.json().get("info"))
            image.save('output.png', 'PNG')
            time.sleep(0.1)
            await message.channel.send(file=discord.File('output.png'), reference=message)

    async def on_message(self, message):
        if message.author == self.user:
            return
        if not message.guild and not config["bot"]["dms"]:
            return
        mentions = [user.id for user in message.mentions]
        if message.guild:
            if not self.user.id in mentions:
                return
        for mention in mentions:
            Username = await self.fetch_user(mention)
            message.content = message.content.replace(f'<@{mention}>', str(Username))
        # Store the message in the appropriate deque
        self.add_message(message.channel.id, message.author.name, message.content)
        # Store the message in the appropriate deque for determiner
        self.add_message_determiner(message.channel.id, message.author.name, message.content)
        cap_removed_message = message.content.casefold()
        trigger_words = 'show','image','generate','create','draw','illustrate','make','produce','selfi','selfie','selfy','picture','photo','photograph','render','take','paint','painting','capture','compose','design','sketch','depict'
        if any(self.is_trigger_word(word, trigger_words) for word in cap_removed_message.split()):
            prompt_starter = config["prompt"]["starter_determiner"]
            prompt_ender = config["prompt"]["ender_determiner"]
            last_message = '\n'.join(self.channel_messages[message.channel.id])
            Final_Prompt = f"{prompt_starter}\n{last_message}\n{prompt_ender}"
            async with self.lock:
                async with message.channel.typing():
                    determiner_reply = await self.send_to_oobabooga_bot(Final_Prompt, 'chat')
            self.add_message(message.channel.id, self.user.name, determiner_reply)
            if determiner_reply.casefold() == 'image':
                if not message.guild and not config["bot"]["dm_images"]:
                    await message.channel.send('The owner of this bot has disabled image generation in direct messages',reference=message)
                    return
                if not config["bot"]["images"]:
                    await message.channel.send('The owner of this bot has disabled image generation',reference=message)
                    return
                prompt_starter = config["prompt"]["starter_nouns"]
                prompt_ender = config["prompt"]["ender_nouns"]
                last_three_messages = '\n'.join(self.channel_messages[message.channel.id])
                Final_Prompt = f"{prompt_starter}\n{last_three_messages}\n{prompt_ender}"
                async with self.lock:  
                    generation_nouns = await self.send_to_oobabooga_bot(Final_Prompt, 'nouns')
                Nouns_first_line = generation_nouns.split("\n")[0]
                await self.generate_and_send_image(message, Nouns_first_line, config)
                return
        Botname = self.user.name
        prompt_starter = config["prompt"]["starter_chatbot"]
        prompt_starter_botnamed = prompt_starter.replace('Botname',Botname)
        prompt_ender = config["prompt"]["ender_chatbot"]
        prompt_ender_botnamed = prompt_ender.replace('Botname',Botname)
        last_five_messages = '\n'.join(self.channel_messages[message.channel.id])
        Final_Prompt = f"{prompt_starter_botnamed}\n{last_five_messages}\n{prompt_ender_botnamed}"
        async with self.lock:  
            async with message.channel.typing():
                bot_reply = await self.send_to_oobabooga_bot(Final_Prompt, 'chat')
        # Send the Oobabooga bot's reply back to the channel
        bot_reply_text = f'{bot_reply}'
        first_line = bot_reply_text.split("\n")[0]
        await message.channel.send(first_line,reference=message)
        # Store the bot's reply in the deque
        self.add_message(message.channel.id, self.user.name, first_line)

    async def send_to_oobabooga_bot(self, Final_Prompt, params_name):
        ooburl = config["bot"]["ooburl"]
        oobApiEndpoint = '/api/v1/generate'
        apiUrl = f'{ooburl}{oobApiEndpoint}'
        #terrible way to do this but it works and changing it breaks it
        parameters = {
        'prompt': Final_Prompt,
        'max_new_tokens': config["oobparams"][params_name]['max_new_tokens'],
        'do_sample': config["oobparams"][params_name]['do_sample'],
        'temperature': config["oobparams"][params_name]['temperature'],
        'top_p': config["oobparams"][params_name]['top_p'],
        'typical_p': config["oobparams"][params_name]['typical_p'],
        'repetition_penalty': config["oobparams"][params_name]['repetition_penalty'],
        'encoder_repetition_penalty': config["oobparams"][params_name]['encoder_repetition_penalty'],
        'top_k': config["oobparams"][params_name]['top_k'],
        'num_beams': config["oobparams"][params_name]['num_beams'],
        'penalty_alpha': config["oobparams"][params_name]['penalty_alpha'],
        'min_length': config["oobparams"][params_name]['min_length'],
        'length_penalty': config["oobparams"][params_name]['length_penalty'],
        'no_repeat_ngram_size': config["oobparams"][params_name]['no_repeat_ngram_size'],
        'early_stopping': config["oobparams"][params_name]['early_stopping'],
        'custom_stopping_strings': config["oobparams"][params_name]['custom_stopping_strings'],
        'seed': config["oobparams"][params_name]['seed'],
        'add_bos_token': config["oobparams"][params_name]['add_bos_token'],
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(apiUrl, json=parameters) as response:
                    result = await response.json()
            except Exception as e:
                print(f'Error sending message to Oobabooga server: {e}')
                return 'Error communicating with Oobabooga bot.'
        try:
            bot_reply = result['results'][0]['text']
        except KeyError:
            print('No response from Oobabooga server.')
            return 'Oobabooga bot did not respond.'
        return bot_reply

if __name__ == '__main__':
    with open("config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file)
    token = config["bot"]["token"]
    intents = discord.Intents.all()
    intents.typing = False
    intents.presences = False

    bot = ChatBot(intents=intents)
    bot.run(token)
