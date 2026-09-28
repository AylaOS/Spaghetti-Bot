# Riot API client: requests, rate limits, retries
import asyncio
from urllib.parse import quote

import aiohttp

class Error(Exception):
    def __init__(self, status, message):
        super().__init__(f"Riot API error {status}: {message}")
        self.status = status

class RiotClient:
    def __init__(self, api_key, platform, region, max_retries=3):
        self.api_key = api_key
        self.platform_url = f"https://{platform}.api.riotgames.com" #league-v4
        self.region_url = f"https://{region}.api.riotgames.com" #account-v1

        self.max_retries = max_retries
        self._session = None

    @classmethod
    def from_config(cls): #fetch required fields from .env
        from bot import config

        return cls(config.RIOT_API_KEY, config.PLATFORM, config.REGION)

    async def start(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"X-Riot-Token": self.api_key},
                timeout=aiohttp.ClientTimeout(total=10)
            )
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *exc):
        await self.close()

    async def _get(self, url):
        if self._session is None or self._session.closed:
            raise RuntimeError("RiotClient not started. Call start() first.")

        for attempt in range(self.max_retries +1):
            async with self._session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                if response.status == 404:
                    return None
                if response.status in (401, 403):
                    raise Error(response.status, "API key rejected. Check RIOT_API_KEY in .env")

                retries_left = attempt < self.max_retries
                if response.status == 429 and retries_left:
                    await asyncio.sleep(int(response.headers.get("Retry-After",1)))
                    continue
                if response.status >= 500 and retries_left:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise Error(response.status, await response.text())
            
    # account-v1 endpoint
    async def get_account(self, game_name, tagLine):
        url = (
            f"{self.region_url}/riot/account/v1/accounts/by-riot-id/"
            f"{quote(game_name)}/{quote(tagLine)}"
        )
        return await self._get(url)

    # league-v4 endpoints
    async def get_ranked_entries(self, puuid):
        #all ranked queue entries for a player; if unranked shows empty
        url = f"{self.platform_url}/lol/league/v4/entries/by-puuid/{puuid}"
        return await self._get(url) or []

    async def get_solo_rank(self, puuid):
        #all solo/duo entries w/ tier, rank, leaguePoints, wins, losses; if unkraed shows empty
        for entry in await self.get_ranked_entries(puuid):
            if entry["queueType"] == "RANKED_SOLO_5x5":
                return entry
        return None

#manual test
async def _demo():
    from bot import config

    async with RiotClient.from_config() as riot:
        for name, tag in config.PLAYERS:
            account = await riot.get_account(name, tag)
            if account is None:
                print(f"{name}#{tag}: account not found")
                continue

            rank = await riot.get_solo_rank(account["puuid"])
            display = f"{account['gameName']}#{account['tagLine']}"

            if rank is None:
                print(f"{display}: unranked")
            else:
                print(
                    f"{display}: {rank['tier']} {rank['rank']} "
                    f"{rank['leaguePoints']} LP ({rank['wins']}W/{rank['losses']}L)"
                    )
                
if __name__ == "__main__":
    asyncio.run(_demo())


