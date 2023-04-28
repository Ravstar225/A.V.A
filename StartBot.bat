@echo off
call python -m pip install --upgrade pip >nul

call python -c "import aiohttp" 2>nul || call python -m pip install aiohttp >nul

call python -c "import discord" 2>nul || call python -m pip install discord >nul

call python -c "import requests" 2>nul || call python -m pip install requests >nul

call python -c "import yaml" 2>nul || call python -m pip install PyYAML >nul

call python -c "from fuzzywuzzy import process" 2>nul || call python -m pip install fuzzywuzzy >nul

call python -c "from PIL import Image, PngImagePlugin" 2>nul || call python -m pip install Pillow >nul

echo All required modules have been checked and installed if necessary.
python MainLoop.py