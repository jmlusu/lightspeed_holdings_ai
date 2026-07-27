import pytest

from lightspeed_agents.memory.search import keyword_search
from lightspeed_agents.memory.models import MemoryEntry


def _make_entries(contents):
    return [MemoryEntry(content=c) for c in contents]


def test_keyword_search_basic():
    entries = _make_entries(
        [
            "deploy the API to staging",
            "fix the login bug",
            "deploy the database migration",
        ]
    )
    results = keyword_search(entries, "deploy")
    assert len(results) == 2
    assert all("deploy" in e.content.lower() for e in results)


def test_keyword_search_no_results():
    entries = _make_entries(["hello world", "foo bar"])
    results = keyword_search(entries, "deploy")
    assert len(results) == 0


def test_keyword_search_limit():
    entries = _make_entries([f"item {i} deploy test" for i in range(20)])
    results = keyword_search(entries, "deploy", limit=5)
    assert len(results) == 5


def test_keyword_search_relevance_ordering():
    entries = [
        MemoryEntry(content="deploy deploy deploy"),
        MemoryEntry(content="deploy once"),
        MemoryEntry(content="no match here"),
    ]
    results = keyword_search(entries, "deploy")
    assert results[0].content == "deploy deploy deploy"


def test_keyword_search_access_count_boost():
    e1 = MemoryEntry(content="deploy the thing", access_count=0)
    e2 = MemoryEntry(content="deploy the thing", access_count=10)
    results = keyword_search(entries=[e1, e2], query="deploy")
    assert results[0].access_count == 10


def test_keyword_search_empty_query():
    entries = _make_entries(["hello"])
    results = keyword_search(entries, "")
    assert len(results) == 0
