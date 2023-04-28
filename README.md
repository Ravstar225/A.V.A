# INFO
Advanced local chat and image bot for Discord. This bot uses Oobabooga and stable diffusion as the backend for a highly customizable discord chat bot that can generate images. Links to our [demo server](https://discord.gg/USwkJprNpN) or to [add to your server](https://discord.com/api/oauth2/authorize?client_id=1100557036820889610&permissions=100352&scope=bot). 

# INTALLATION INSTRUCTIONS
---Warning: This is incredibly vram intensive, minimum recommended is 16GB---
1. Download python 3.10 (verified working with 3.10.9 and 3.10.6)
2. Install [automatic1111](https://github.com/AUTOMATIC1111/stable-diffusion-webui) and [oobabooga](https://github.com/oobabooga/one-click-installers) if you haven't already
4. Install [gpt4-x-alpaca](https://huggingface.co/chavinlo/gpt4-x-alpaca) and a model of your choosing for stable diffusion (I recommend [this](https://civitai.com/models/7371?modelVersionId=46846)
5. Run both automatic1111 and Oobabooga with the `--api` flag 
6. Clone the repository into a directory with `git clone https://github.com/Ravstar225/A.V.A`
7. Fill in config.yaml with your discord bot's token and links to your stable diffusion and obabooga instances
8. Run StartBot.bat
9. Enjoy!

#Other models
Other text models such as Vicuna can be used, but they might produce weird responses as the paramaters are and formatting are not natively correct for them. If you chanage the text model you're using, it is recommended that you also change the parameters in the config.yaml file.
As with text models, any model compatible with stable diffusion can be used, and if you aren't happy with the way it looks I recommend playing around with the parameters.
