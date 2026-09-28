import logging

import discord
from discord.ext import commands

from bot import config
from bot.riot import RiotClient

log = logging.getLogger(__name__)

EXTENSIONS = [
    "bot.cogs.refresher",
    "bot.cogs.leaderboard",
]

class SpaghettiBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned, #SLASH commands
                         intents=discord.Intents.default())
        self.riot = RiotClient.from_config()
        self.ranks = {}
        self.baseline = {}
        self.last_refresh = None

    async def setup_hook(self):
        #runs once before bot connects
        await self.riot.start()
        for ext in EXTENSIONS:
            await self.load_extension(ext)

        synced = await self.tree.sync()
        log.info("Synced %d slash command(s)", len(synced))

    async def on_ready(self):
        log.info("Logged in as %s", self.user)

    async def close(self):
        await self.riot.close()
        await super().close()

def main():
    SpaghettiBot().run(config.DISCORD_TOKEN, root_logger=True)

if __name__ == "__main__":
    main()