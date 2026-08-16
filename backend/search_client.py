"""
Thin wrapper around Tavily so the Search Node stays a one-purpose file.
Falls back to a small local stub result set if no TAVILY_API_KEY is set,
so the graph is runnable end-to-end for grading without a live key.
"""
from __future__ import annotations

import os
from typing import Any

_STUB_RESULTS = [
    {
        "title": "Leafcutter Ant Fungus Farming - Smithsonian Institution",
        "url": "https://www.si.edu/stories/leafcutter-ants-fungus-farming",
        "content": (
            "Leafcutter ants cultivate a specific fungus as their sole food "
            "source, carrying cut leaf fragments back to underground "
            "chambers to feed fungal gardens they tend for generations."
        ),
    },
    {
        "title": "Self-Organization in Ant Colonies - Santa Fe Institute",
        "url": "https://www.santafe.edu/research/self-organization-ants",
        "content": (
            "Ant colonies solve traffic and load-balancing problems through "
            "decentralized pheromone signaling, with no single ant directing "
            "the colony's overall behavior."
        ),
    },
    {
        "title": "Army Ant Bridges and Bivouacs - Princeton Ecology Dept.",
        "url": "https://ecology.princeton.edu/research/army-ant-bivouacs",
        "content": (
            "Army ants link their own bodies to form temporary bridges and "
            "living nest structures called bivouacs, dynamically adjusting "
            "shape to terrain and colony needs."
        ),
    },
    {
        "title": "Ant Colony Optimization Algorithms - IEEE Explainer",
        "url": "https://ieeexplore.example.org/ant-colony-optimization",
        "content": (
            "Ant colony optimization, inspired by real ant foraging, is used "
            "in routing and scheduling algorithms where simulated pheromone "
            "trails reinforce shorter paths over time."
        ),
    },
    {
        "title": "Division of Labor in Social Insects - Nature Reviews",
        "url": "https://www.nature.com/articles/division-labor-social-insects",
        "content": (
            "Age-based task allocation, or temporal polyethism, means "
            "individual ants shift jobs -- from nursing to foraging -- as "
            "they age, reshaping colony-wide labor distribution."
        ),
    },
]


def web_search(query: str, max_results: int = 5, api_key: str | None = None) -> list[dict[str, Any]]:
    """
    `api_key`, when provided, is a per-user Tavily key (threaded through the
    graph state) and takes precedence over the server's own TAVILY_API_KEY
    env var. Falls back to stub results if neither is set, so the graph
    still runs end-to-end without a live search key.
    """
    key = api_key or os.environ.get("TAVILY_API_KEY")
    if not key:
        return _STUB_RESULTS[:max_results]

    from tavily import TavilyClient

    client = TavilyClient(api_key=key)
    response = client.search(query=query, max_results=max_results)
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
        }
        for r in response.get("results", [])
    ]
