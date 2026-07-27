from lightspeed_agents.memory.models import MemoryEntry


def keyword_search(
    entries: list[MemoryEntry],
    query: str,
    limit: int = 10,
) -> list[MemoryEntry]:
    terms = query.lower().split()
    if not terms:
        return []

    scored = []
    for entry in entries:
        content_lower = entry.content.lower()
        score = 0
        for term in terms:
            count = content_lower.count(term)
            if count > 0:
                score += count * (1 + entry.access_count * 0.1)
        if score > 0:
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored[:limit]]
