"""Bounded orthographic recovery for keyword and request matching.

Only unique one-edit candidates in the configured allowlist are accepted.
Deletion indexes make lookups depend on token length, not thread x vocabulary
comparisons. No network call, additional model or runtime dependency is needed.
"""

import re
import unicodedata
from functools import lru_cache
from typing import Any

from escalation_engine.config import ESCALATION_CONFIG


def _tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize('NFKD', text.lower())
    return re.findall(r'[a-z]+', ''.join(
        char for char in normalized if not unicodedata.combining(char)
    ))


@lru_cache(maxsize=8)
def _known_words(entries: tuple[str, ...]) -> frozenset[str]:
    return frozenset(word for entry in entries for word in _tokens(entry))


@lru_cache(maxsize=8)
def _index(terms: tuple[str, ...]) -> tuple[set[str], dict[str, set[str]]]:
    vocabulary = set(terms)
    deletions: dict[str, set[str]] = {}
    for term in vocabulary:
        for position in range(len(term)):
            key = term[:position] + term[position + 1:]
            deletions.setdefault(key, set()).add(term)
    return vocabulary, deletions


def _one_edit(left: str, right: str) -> bool:
    if len(left) == len(right):
        differences = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
        if len(differences) == 1:
            return True
        if len(differences) == 2:
            a, b = differences
            return b == a + 1 and left[a] == right[b] and left[b] == right[a]
        return False
    if len(left) > len(right):
        left, right = right, left
    if len(right) != len(left) + 1:
        return False
    mismatch = next((i for i, (a, b) in enumerate(zip(left, right)) if a != b), len(left))
    return left[mismatch:] == right[mismatch + 1:]


@lru_cache(maxsize=4096)
def _candidate(token: str, terms: tuple[str, ...]) -> str | None:
    vocabulary, deletions = _index(terms)
    candidates = set(deletions.get(token, ()))
    for position in range(len(token)):
        key = token[:position] + token[position + 1:]
        if key in vocabulary:
            candidates.add(key)
        candidates.update(deletions.get(key, ()))
    matches = {term for term in candidates if _one_edit(token, term)}
    return next(iter(matches)) if len(matches) == 1 else None


def correct_spelling(text: str) -> tuple[str, list[dict[str, Any]]]:
    """Return matching text and edits with offsets in the original input text.

    Callers retain the original cleaned body. Context checks run on the whole
    matching text so corrections cannot bypass negation or resolution filters.
    """
    config = ESCALATION_CONFIG['spelling']
    if not config['enabled']:
        return text, []
    terms = tuple(sorted(set(config['terms'])))
    # Existing literal vocabulary always takes precedence over a fuzzy guess.
    literals = tuple(
        phrase
        for topic in ESCALATION_CONFIG['topics'].values()
        for field in ('keywords', 'phrases', 'critical_phrases')
        for phrase in topic.get(field, [])
    )
    known = _known_words(terms + tuple(config['protected_terms']) + literals)
    corrections = []

    def replace(match: re.Match[str]) -> str:
        token = match.group()
        if (token in known or not token.isascii() or not token.isalpha()
                or not config['min_token_length'] <= len(token) <= config['max_token_length']):
            return token
        replacement = _candidate(token, terms)
        if replacement is None:
            return token
        corrections.append({
            'original': token,
            'replacement': replacement,
            'distance': 1,
            'matchType': 'orthographic',
            'start': match.start(),
            'end': match.end(),
        })
        return replacement

    return re.sub(r'\b\w+\b', replace, text), corrections
