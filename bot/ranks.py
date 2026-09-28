#rank math and formatting
TIERS = [
    "IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD",
    "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER",
]
DIVISIONS = {"IV": 0, "III": 1, "II": 2, "I": 3}
APEX_START = TIERS.index("MASTER")


def rank_score(entry):
    tier = TIERS.index(entry["tier"])
    if tier >= APEX_START:
        return APEX_START * 400 + entry["leaguePoints"]
    return tier * 400 + DIVISIONS[entry["rank"]] * 100 + entry["leaguePoints"]


def format_rank(tier, division):
    if TIERS.index(tier) >= APEX_START:
        return tier.title()
    return f"{tier.title()} {division}"