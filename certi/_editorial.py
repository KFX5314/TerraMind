"""Notation-only differences between regulation versions that are not amendments."""

EDITORIAL = [
    (r"\s*%", " per cent"),
    (r"\bpercent\b", "per cent"),
    (r"\bseconds?\b", "s"),
    (r"\bmetres?\b", "m"),
    (r"\bkilometres? per hour\b", "km/h"),
    (r"\bparagraphs?\b", "paragraph"),
]
