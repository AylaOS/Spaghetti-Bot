import os

from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
RIOT_API_KEY = os.environ["RIOT_API_KEY"]
PLATFORM = os.getenv("PLATFORM", "na1") #defaults to na1 platform
REGION = os.getenv("REGION","americas") #defaults to americas
REFRESH_MINUTES = int(os.getenv("REFRESH_MINUTES", "15")) #defaults to every 15 mins
LEADERBOARD_CHANNEL_ID = os.environ["LEADERBOARD_CHANNEL_ID"]

PLAYERS=[
    ("Ayla","BOT"), #<name>,<tag>
    #("BedroomAthletics","V21"),
    ("FOOT DIVE","DOOM"),
    ("SNAIL TRAIL", "SQRT"),
    ("WawaSkittletit", "WEEWA"),
    ("Open Book", "NA1"),
    ("AXTER","NA1"),
    ("ShacoGuy","NA99"),
    ("noctivor","NA1"),
    ("Sukuna","TAWG")
]