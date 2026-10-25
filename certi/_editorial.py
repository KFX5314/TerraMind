"""Notation-only differences between regulation versions that are not amendments."""

EDITORIAL = [
    (r"\s*%", " per cent"),
    (r"\bpercent\b", "per cent"),
    (r"\bseconds?\b", "s"),
    (r"\bmetres?\b", "m"),
    (r"\bkilometres? per hour\b", "km/h"),
    (r"\bparagraphs?\b", "paragraph"),
    # number words written as digits ("three" -> "3")
    (r"\bone\b", "1"), (r"\btwo\b", "2"), (r"\bthree\b", "3"), (r"\bfour\b", "4"), (r"\bfive\b", "5"),
    (r"\bsix\b", "6"), (r"\bseven\b", "7"), (r"\beight\b", "8"), (r"\bnine\b", "9"), (r"\bten\b", "10"),
    # leading connectors that do not change an obligation ("In addition, the system shall" == "The system shall")
    (r"\b(?:in addition|furthermore|moreover|additionally)\s*,\s*(?:further\s+|the\s+)?", "the "),
]
