"""Rarity tiers within one prompt: rank by Wikidata language-page count, split into five equal groups."""
from generator.dayfile import TIERS

ORDER = list(TIERS)  # most obvious first
DEFAULT_TIER = "raiz"


def assign_tiers(fame: dict[str, int | None]) -> dict[str, str]:
    """fame maps answer id to language-page count, or None when the identity isn't trusted."""
    ranked = sorted((count for count in fame.values() if count is not None), reverse=True)
    # Index of the last answer with each count, so ties take the rarer group.
    last_position = {count: position for position, count in enumerate(ranked)}
    tiers = {}
    for answer, count in fame.items():
        if count is None:
            tiers[answer] = DEFAULT_TIER
        else:
            group = last_position[count] * len(ORDER) // len(ranked)
            tiers[answer] = ORDER[min(group, len(ORDER) - 1)]
    return tiers
