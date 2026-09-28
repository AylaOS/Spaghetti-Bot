#background task: fetches every player's rank on a timer and stores it on the bot.
import logging

import discord
from discord.ext import commands, tasks

from bot import config
from bot.ranks import rank_score

log = logging.getLogger(__name__)


class Refresher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.accounts = {} #<name><tag> looked up once
        self.refresh.start()

    def cog_unload(self):
        self.refresh.cancel()

    @tasks.loop(minutes=config.REFRESH_MINUTES)
    async def refresh(self):
        for name, tag in config.PLAYERS:
            try:
                await self.update_player(name, tag)
            except Exception:
                #updates regardless of 1 unfetched players
                log.exception("Failed to refresh %s#%s", name, tag)
        self.bot.last_refresh = discord.utils.utcnow()
        log.info("Refreshed %d player(s)", len(self.bot.ranks))
        #tells cog rank is updated
        self.bot.dispatch("ranks_updated")

    @refresh.before_loop
    async def before_refresh(self):
        await self.bot.wait_until_ready()

    async def update_player(self, name, tag):
        riot = self.bot.riot

        account = self.accounts.get((name, tag))
        if account is None:
            account = await riot.get_account(name, tag)
            if account is None:
                log.warning("Riot ID not found: %s#%s", name, tag)
                return
            self.accounts[(name, tag)] = account

        puuid = account["puuid"]
        entry = await riot.get_solo_rank(puuid)

        player = {
            "riot_id": f"{account['gameName']}#{account['tagLine']}",
            "ranked": entry is not None,
        }
        if entry is not None:
            score = rank_score(entry)
            player.update(
                tier=entry["tier"],
                division=entry["rank"],
                lp=entry["leaguePoints"],
                wins=entry["wins"],
                losses=entry["losses"],
                score=score,
            )
            #for new players, baseline score recorded
            self.bot.baseline.setdefault(puuid, score)

        self.bot.ranks[puuid] = player


async def setup(bot):
    await bot.add_cog(Refresher(bot))