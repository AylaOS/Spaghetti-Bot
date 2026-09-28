#leaderboard: shows ranks from last refresh (courtesy of refresher). does not call Riot directly
import logging

import discord
from discord.ext import commands

from bot import config
from bot.ranks import format_rank

log = logging.getLogger(__name__)

TITLE = "Solo/Duo Leaderboard"
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message = None
        self.last_snapshot = None

    @commands.Cog.listener()
    async def on_ranks_updated(self):
        snapshot = self.snapshot()
        if snapshot == self.last_snapshot:
            return  #since nothing changed, don't touch message

        try:
            await self.publish(self.build_embed())
            self.last_snapshot = snapshot
        except discord.HTTPException:
            log.exception("Failed to post leaderboard.")

    def snapshot(self):
        return tuple(sorted(
            (puuid, p["riot_id"], p.get("score"), p.get("wins"), p.get("losses"))
            for puuid, p in self.bot.ranks.items()
        ))

    async def get_channel(self):
        channel_id = config.LEADERBOARD_CHANNEL_ID
        return self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)

    async def find_message(self, channel):
        # updates message instead of posting new one
        async for message in channel.history(limit=50):
            if message.author == self.bot.user and message.embeds and message.embeds[0].title == TITLE:
                return message
        return None

    async def publish(self, embed):
        channel = await self.get_channel()

        if self.message is None:
            self.message = await self.find_message(channel)

        if self.message is not None:
            try:
                await self.message.edit(embed=embed)
                return
            except discord.NotFound:
                self.message = None  #if message is deleted; post new one

        self.message = await channel.send(embed=embed)

    def build_embed(self):
        players = list(self.bot.ranks.items())
        ranked = sorted(
            (p for p in players if p[1]["ranked"]),
            key=lambda p: p[1]["score"],
            reverse=True,
        )
        unranked = [p for p in players if not p[1]["ranked"]]

        lines = []
        for place, (puuid, p) in enumerate(ranked, start=1):
            prefix = MEDALS.get(place, f"`{place}.`")
            rank = format_rank(p["tier"], p["division"])
            games = p["wins"] + p["losses"]
            winrate = round(100 * p["wins"] / games) if games else 0

            lines.append(
                f"{prefix} **{p['riot_id']}**\n"
                f"{rank} · {p['lp']} LP · {winrate}% WR ({p['wins']}W/{p['losses']}L)"
                f"{self.format_change(puuid, p['score'])}"
            )

        if unranked:
            names = ", ".join(p["riot_id"] for _, p in unranked)
            lines.append(f"\n*Unranked:* {names}")

        embed = discord.Embed(
            title=TITLE,
            description="\n\n".join(lines) or "No data yet.",
            color=discord.Color.gold(),
        )
        embed.set_footer(text="LP change since tracking started · Last updated")
        embed.timestamp = self.bot.last_refresh
        return embed

    def format_change(self, puuid, score):
        change = score - self.bot.baseline.get(puuid, score)
        if change > 0:
            return f" · 🟢 +{change}"
        if change < 0:
            return f" · 🔴 {change}"
        return ""


async def setup(bot):
    await bot.add_cog(Leaderboard(bot))