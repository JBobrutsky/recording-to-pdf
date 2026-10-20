# -*- coding: utf-8 -*-
"""Private people file: who is who in your meetings.

Markdown, one `## <full name>` section per person with `- key: value` lines
(zoom, en, gender, aka, team, role, works on, notes). See
examples/people.example.md. The real file holds colleagues' details: keep it
outside any repo and point R2R_PEOPLE at it.
"""
import os, re


def load(path=None):
    path = path or os.environ.get("R2R_PEOPLE")
    if not path or not os.path.exists(os.path.expanduser(path)):
        return []
    people, cur = [], None
    for line in open(os.path.expanduser(path), encoding="utf-8"):
        if line.startswith("## "):
            cur = {"name": line[3:].strip()}; people.append(cur)
        elif cur is not None and (m := re.match(r"\s*-\s*([\w ]+?)\s*:\s*(.*)", line)):
            cur[m.group(1).lower()] = m.group(2).strip()
    return people


def _aliases(p):
    return [a.strip() for k in ("zoom", "en", "aka") for a in p.get(k, "").split(",") if a.strip()]


def prompt(people):
    """Names for whisper's initial_prompt (it biases spelling, not content)."""
    names = []
    for p in people:
        names += [p["name"]] + [a for a in p.get("aka", "").split(",") if a.strip()]
    return ", ".join(dict.fromkeys(n.strip() for n in names))[:600]


def canonical(people):
    """Lower-cased Zoom/English/nickname → the name to write in the review."""
    return {a.lower(): p["name"] for p in people for a in _aliases(p)}
