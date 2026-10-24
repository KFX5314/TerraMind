"""Deterministic 'modified' texts: apply the old->new source diff to the old requirement text.

The expert's new_text is the old requirement with the amended words swapped in, so we do the same in code and only
fall back to the model when an edited phrase cannot be located in the requirement."""

from __future__ import annotations

import re
from difflib import SequenceMatcher


def _norm(tok: str) -> str:
    return re.sub(r"[^0-9a-z%°]+", "", tok.casefold())


def _find(seq: list[str], sub: list[str], start: int = 0) -> int:
    """Index of the token subsequence `sub` in `seq` (punctuation/case-insensitive), or -1."""
    ns, nsub = [_norm(t) for t in seq], [_norm(t) for t in sub]
    nsub = [t for t in nsub if t]
    if not nsub:
        return -1
    for i in range(start, len(ns) - len(nsub) + 1):
        window = [t for t in ns[i:i + len(nsub)] if t]
        if window == nsub:
            return i
    return -1


def apply_diff(req_text: str, old_src: str, new_src: str) -> str | None:
    """Return the requirement text with the source amendments applied; None if an edit cannot be anchored.
    Returns the unchanged text when no amendment touches the requirement's words."""
    a, b, req = old_src.split(), new_src.split(), req_text.split()
    changed = False
    for op, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        old_phrase, new_phrase = a[i1:i2], b[j1:j2]
        if op in ("replace", "delete"):
            pos = _find(req, old_phrase)
            if pos < 0:
                # the edited phrase is not part of this requirement: not our change, unless its context is
                ctx = a[max(0, i1 - 2):i2 + 2]
                if _find(req, ctx) >= 0:
                    return None  # requirement spans the context but not the exact phrase: let the model decide
                continue
            req = req[:pos] + new_phrase + req[pos + len(old_phrase):]
            changed = True
        else:  # insert: anchor on the preceding and following words of the source
            before, after = a[max(0, i1 - 2):i1], a[i1:i1 + 2]
            pos_both = _find(req, before + after) if before and after else -1
            if pos_both >= 0:
                at = pos_both + len(before)
            else:
                pos_b = _find(req, before) if before else -1
                pos_a = _find(req, after) if after else -1
                if pos_b >= 0 and (pos_a < 0 or pos_a >= pos_b):
                    at = pos_b + len(before)
                elif pos_a >= 0:
                    at = pos_a
                else:
                    continue
            req = req[:at] + new_phrase + req[at:]
            changed = True
    text = " ".join(req)
    # tidy punctuation produced by splicing ("standstill. and," -> keep source punctuation as is)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    return text if changed else req_text
