# content.json

```jsonc
{
  "lang": "he",              // he | en ...
  "rtl": true,               // default: lang == "he"
  "title": "...",
  "subtitle": "...",
  "meta": ["speaker · date", "duration · source"],
  "timestamps": false,       // default false: [m:ss] refs and "זמן"/"Time" columns are stripped
  "meeting": {               // only for meetings (not public talks); see SKILL.md "Meetings"
    "context": "work",       // work | personal | public
    "org": "Acme Corp",      // optional label shown on the banner
    "date": "2026-10-18",
    "participants": ["דנה כהן", "..."],
    "summary": "2–3 sentences: what the meeting was about and what was decided",
    "decisions": ["..."],
    "actions": [{"owner": "דנה", "task": "...", "due": "יום ד׳", "status": "פתוח"}],
    "open_questions": ["..."]
  },
  "blocks": [
    {"kind": "h1",   "text": "1. תקציר מנהלים"},
    {"kind": "body", "text": "פסקה.\n\nפסקה שנייה."},
    {"kind": "bullets", "items": [["מוביל: ", "שאר המשפט"], "פריט רגיל"]},
    {"kind": "table", "headers": ["זמן","נושא"], "rows": [["0:00","פתיחה"]],
                      "widths": [1.2, 5.0]},
    {"kind": "image", "file": "k_012.png", "caption": "...", "width": 6.3},
    {"kind": "callout", "text": "...", "label": "שימו לב"},
    {"kind": "quote", "text": "ציטוט", "by": "— שם"},
    {"kind": "pagebreak"}
  ]
}
```

Rules that keep the document good:
- Interleave `image` blocks with the argument; never dump them in an appendix.
- Every quote must exist verbatim in the transcript. Timestamps are optional: write
  `[m:ss]` freely while drafting; render strips them unless `--timestamps` /
  `"timestamps": true`.
- Put every slide of a supplied deck in as an image next to its section — never
  replace slides with re-typed text.
- Bold lead on bullets carries the claim, the rest carries the evidence.
- Open with: about + disclaimer, then executive summary, then detail, then actions.
- With `meeting`, render adds the context banner on top and "Decisions" +
  "Assignments by owner" at the end, and writes `out/record.json` / `record.md`
  (plus a row in `--index`). Don't repeat those sections by hand.
